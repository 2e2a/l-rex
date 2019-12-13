import csv
from io import StringIO

from django import forms


DEFAULT_DELIMITER = ';'
DEFAULT_QUOTING = csv.QUOTE_MINIMAL
DEFAULT_DIALECT = {
    'delimiter': DEFAULT_DELIMITER,
    'quoting': DEFAULT_QUOTING,
    'has_header': True,
}


def read_file(form_cleaned_data):
    file = form_cleaned_data['file']
    try:
        data = file.read().decode('utf-8')
    except UnicodeDecodeError:
        file.seek(0)
        data = file.read().decode('latin-1')
    return data


def seek_file(form_cleaned_data):
    form_cleaned_data['file'].seek(0)


def sniff(data):
    data_len = len(data)
    return data[:1000 if data_len > 1000 else data_len]

def get_min_columns(form_cleaned_data):
    min_columns = 1
    for field, data in form_cleaned_data.items():
        if '_column' in field:
            min_columns = max(min_columns, data)
    return min_columns


def detect_dialect(data, form_cleaned_data, int_column_names=None, user_delimiter=None):

    SNIFF_ROWS = 2

    def _row_column_types_match(row, int_columns):
        for col in int_columns:
            try:
                int(row[col - 1])
            except ValueError:
                return False
        return True

    def _is_row_valid(row, int_columns, min_columns):
        return row and min_columns <= len(row) and _row_column_types_match(row, int_columns)

    def _has_header(first_row, int_columns):
        return not _row_column_types_match(first_row, int_columns)

    try:
        int_columns = [form_cleaned_data[column_name] for column_name in int_column_names]
        min_columns = get_min_columns(form_cleaned_data)
        delimiters = [user_delimiter] if user_delimiter else [';', '\t', ',']
        for delimiter in delimiters:
            reader = csv.reader(StringIO(data), delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
            first_row = next(reader)
            rows = []
            try:
                for _ in range(SNIFF_ROWS):
                    rows.append(next(reader))
            except StopIteration:
                pass
            rows_valid = True
            if len(rows) == 0 and not user_delimiter:
                raise forms.ValidationError('File not big enough to detect format.')
            for row in rows:
                if not _is_row_valid(row, int_columns, min_columns):
                    rows_valid = False
                    break
            if rows_valid:
                has_header = _has_header(first_row, int_columns)
                return delimiter, csv.QUOTE_MINIMAL, has_header
        raise forms.ValidationError('Unsupported CSV format.')
    except (UnicodeDecodeError, TypeError):
        raise forms.ValidationError(
            'Unsupported file encoding or format. Use UTF-8 or Latin-1 and check the CSV for errors.'
        )
    except csv.Error:
        raise forms.ValidationError('Unsupported CSV format.')
