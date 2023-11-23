from datetime import datetime
import gspread
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
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
            # Membuat DataFrame dari data
            df_dp = pd.DataFrame(data)

            # Mengonversi kolom tanggal menjadi tipe datetime
            df_dp['Tanggal Pickup'] = pd.to_datetime(df_dp['Tanggal Pickup'], format='%d/%m/%Y')

            # Buat kolom bulan dari tanggal
            df_dp['Bulan'] = df_dp['Tanggal Pickup'].dt.strftime("%B")

            # Filter data berdasarkan bulan Juli, Agustus, September, dan Oktober
            start_date = datetime(2023, 7, 1)
            end_date = datetime(2023, 10, 31)
            filtered_data = df_dp[(df_dp['Tanggal Pickup'] >= start_date) & (df_dp['Tanggal Pickup'] <= end_date)]

            # Mengurutkan data berdasarkan RS/Klinik dan Tanggal Pickup
            sorted_data = filtered_data.sort_values(by=['Tanggal Pickup', 'RS/Klinik'])

            # Membuat ringkasan berdasarkan RS/Klinik
            summary = sorted_data.groupby([ 'ID Sample', 'Tanggal Pickup', 'RS/Klinik'])['ID Sample'].count().reset_index(name='Summary Pembelian')
            return summary
        except Exception as e:
            print(f"Error while generating summary: {str(e)}")
            return None

    #Membuat Pdf
    def export_to_pdf(self, summary, output_filename):
        if summary is None:
            return

        try:
            html_content = summary.to_html(index=False)

            # Open the file in binary mode ('wb')
            with open(output_filename, 'wb') as f:
                pisa.CreatePDF(html_content, dest=f)

            print(f"Summary berhasil disimpan dalam file PDF: {output_filename}")
        except Exception as e:
            print(f"Error while exporting to PDF: {str(e)}")

 # Menampilkan summary dalam card
class SampleCardApp(QWidget):
    def __init__(self, summary):
        super().__init__()
        self.setWindowTitle("Sample Summary Card")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        for index, row in summary.iterrows():
            label_text = f"{row['ID Sample']} - {row['Tanggal Pickup']} - {row['RS/Klinik']}"
            label = QLabel(label_text)
            layout.addWidget(label)

        self.setLayout(layout)

if __name__ == '__main__':
    keyfile = 'key.json'
    spreadsheet_name = '4.1. Generik - Sample'
    worksheet_name = 'Data Sampel'
    output_pdf_filename = 'summary_RS.pdf'

    sample_summary = SampleSummary(keyfile, spreadsheet_name, worksheet_name)
    data = sample_summary.get_data()
    summary = sample_summary.generate_summary(data)

    if summary is not None:
        app = QApplication([])
        card_app = SampleCardApp(summary)
        card_app.show()

        sample_summary.export_to_pdf(summary, output_pdf_filename)

        app.exec_()
