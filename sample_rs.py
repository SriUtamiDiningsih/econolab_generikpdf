from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout, QScrollArea, QComboBox
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

    def generate_summary(self, data, selected_rs=None):
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

            # Apply RS/Klinik filter if selected
            if selected_rs:
                filtered_data = filtered_data[filtered_data['RS/Klinik'] == selected_rs]

            # Mengurutkan data berdasarkan RS/Klinik dan Tanggal Pickup
            sorted_data = filtered_data.sort_values(by=['Tanggal Pickup', 'RS/Klinik'])

            # Membuat ringkasan berdasarkan RS/Klinik
            summary = sorted_data.groupby(['ID Sample', 'Tanggal Pickup', 'RS/Klinik'])['ID Sample'].count().reset_index(name='Summary Pembelian')
            return summary
        except Exception as e:
            print(f"Error while generating summary: {str(e)}")
            return None

    def export_to_pdf(self, summary, output_filename):
        if summary is None:
            return

        try:
            # Membuat PDF dari HTML
            with open(output_filename, "w+b") as pdf_file:
                pdf_file.write(self.html_to_pdf(summary.to_html()))

            print(f"Summary berhasil disimpan dalam file PDF: {output_filename}")
        except Exception as e:
            print(f"Error while exporting to PDF: {str(e)}")

    def html_to_pdf(self, html):
        from io import BytesIO
        from xhtml2pdf import pisa

        # Menghasilkan file PDF menggunakan xhtml2pdf
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

    # Generate and export summary to PDF
    summary = sample_summary.generate_summary(data)

    if summary is not None:
        try:
            # Membuat aplikasi PyQt5
            app = QApplication([])

            main_widget = QWidget()
            main_layout = QGridLayout()

            # Menambahkan QComboBox untuk memfilter RS/Klinik
            rs_combobox = QComboBox()
            rs_combobox.addItem("All")  # Option to show all RS/Klinik
            rs_combobox.addItems(summary['RS/Klinik'].unique())

            def on_rs_combobox_changed():
                selected_rs = rs_combobox.currentText()
                filtered_summary = sample_summary.generate_summary(data, selected_rs)
                update_labels(filtered_summary)

            rs_combobox.currentIndexChanged.connect(on_rs_combobox_changed)

            main_layout.addWidget(rs_combobox, 0, 0, 1, 2)

            scroll_area = QScrollArea()
            scroll_content = QWidget()
            scroll_layout = QGridLayout()
            scroll_content.setLayout(scroll_layout)
            scroll_area.setWidget(scroll_content)
            scroll_area.setWidgetResizable(True)

            main_layout.addWidget(scroll_area, 1, 0, 1, 2)

            main_widget.setLayout(main_layout)
            main_widget.showMaximized()

            def update_labels(filtered_summary):
                # Hapus label yang sudah ada di layout sebelum menambahkan yang baru
                for i in reversed(range(scroll_layout.count())):
                    item = scroll_layout.itemAt(i)
                    if item.widget():
                        item.widget().setParent(None)

                # Menampilkan card perRS
                for i, (index, row) in enumerate(filtered_summary.iterrows()):
                    label_text = f"{row['ID Sample']}\n{row['Tanggal Pickup']}\n{row['RS/Klinik']}"
                    label = QLabel(label_text)
                    label.setFont(QFont("Arial", 12, QFont.Bold))

                    # Penyesuaian label sesuai kebutuhan
                    label.setAlignment(Qt.AlignCenter)
                    label.setStyleSheet("border: 1px solid #000; padding: 10px;")

                    scroll_layout.addWidget(label, i // 2, i % 2)

            update_labels(summary)
            sample_summary.export_to_pdf(summary, output_pdf_filename)

            app.exec_()
        except Exception as e:
            print(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()