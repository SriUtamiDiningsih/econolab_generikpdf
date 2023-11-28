from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout, QScrollArea
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from datetime import datetime
import gspread
import pandas as pd
from xhtml2pdf import pisa

class SampleSummary:
    def __init__(self, keyfile, spreadsheet_name, worksheet_name):
        self.sheet_service = gspread.service_account(filename=keyfile)
        self.df_ds = self.sheet_service.open(spreadsheet_name).worksheet(worksheet_name)

    def get_data(self):
        try:
            data = self.df_ds.get_all_records()
            return data
        except Exception as e:
            print(f"Error while fetching data: {str(e)}")
            return None

    def generate_summary(self, data):
        if data is None:
            return None

        try:
            df_dp = pd.DataFrame(data)
            df_dp['Tanggal Pickup'] = pd.to_datetime(df_dp['Tanggal Pickup'], format='%d/%m/%Y')
            df_dp['Bulan'] = df_dp['Tanggal Pickup'].dt.strftime("%B")

            start_date = datetime(2023, 7, 1)
            end_date = datetime(2023, 10, 31)
            filtered_data = df_dp[(df_dp['Tanggal Pickup'] >= start_date) & (df_dp['Tanggal Pickup'] <= end_date)]
            sorted_data = filtered_data.sort_values(by=['Tanggal Pickup', 'RS/Klinik'])
            summary = sorted_data.groupby(['ID Sample', 'Tanggal Pickup', 'RS/Klinik'])['ID Sample'].count().reset_index(name='Summary Pembelian')
            return summary
        except Exception as e:
            print(f"Error while generating summary: {str(e)}")
            return None

    def export_to_pdf(self, summary, output_filename):
        if summary is None:
            return

        try:
            with open(output_filename, "w+b") as pdf_file:
                pdf_file.write(self.html_to_pdf(summary.to_html()))

            print(f"Summary berhasil disimpan dalam file PDF: {output_filename}")
        except Exception as e:
            print(f"Error while exporting to PDF: {str(e)}")

    def html_to_pdf(self, html):
        from io import BytesIO
        from xhtml2pdf import pisa

        pdf_file = BytesIO()
        pisa.CreatePDF(BytesIO(html.encode('utf-8')), pdf_file)
        return pdf_file.getvalue()

def main():
    keyfile = 'key.json'
    spreadsheet_name = '4.1. Generik - Sample'
    worksheet_name = 'Data Sampel'
    output_pdf_filename = 'summary_RS.pdf'

    sample_summary = SampleSummary(keyfile, spreadsheet_name, worksheet_name)
    data = sample_summary.get_data()
    summary = sample_summary.generate_summary(data)

    if summary is not None:
        try:
            app = QApplication([])

            main_widget = QWidget()
            layout = QGridLayout()

            for i, (index, row) in enumerate(summary.iterrows()):
                label_text = f"{row['ID Sample']}\n{row['Tanggal Pickup']}\n{row['RS/Klinik']}"
                label = QLabel(label_text)
                label.setFont(QFont("Arial", 12, QFont.Bold))

                # Penyesuaian label sesuai kebutuhan
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("border: 1px solid #000; padding: 10px;")

                layout.addWidget(label, i // 2, i % 2)

            scroll_area = QScrollArea()
            scroll_content = QWidget()
            scroll_content.setLayout(layout)
            scroll_area.setWidget(scroll_content)
            scroll_area.setWidgetResizable(True)

            main_widget_layout = QGridLayout()
            main_widget_layout.addWidget(scroll_area)

            main_widget.setLayout(main_widget_layout)
            main_widget.showMaximized()

            sample_summary.export_to_pdf(summary, output_pdf_filename)

            app.exec_()
        except Exception as e:
            print(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()