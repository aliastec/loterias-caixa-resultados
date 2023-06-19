from bs4 import BeautifulSoup
from bs4.element import Tag

# Parse results page to comma-separated values.
def parse_results_page(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')

    csv_contents = ''
    rows = soup.find('table', class_='tabela-resultado').contents
    for row in rows:
        line = ''
        if isinstance(row, Tag) and row.tr != None:
            cells = row.tr.contents
            for cell in cells:
                if cell.string != None:
                    line += '{},'.format(cell.string.strip('\n').replace(',', ''))
                elif len(cell.contents) > 0 and cell.table != None:
                    values_array = '('
                    subrows = cell.table.tbody.contents
                    for subrow in subrows:
                        if isinstance(subrow, Tag):
                            subcells = subrow.contents
                            for subcell in subcells:
                                if subcell.string != None and len(subcell.string.strip()) > 0:
                                    values_array += '[{}]'.format(subcell.string.strip('\n').replace(',', ''))
                    values_array += ')'
                    line += '{},'.format(values_array)
                else:
                    line += ','
            csv_contents += '{}\n'.format(line.rstrip(','))

    return csv_contents.replace('.', '').replace('R$', '')