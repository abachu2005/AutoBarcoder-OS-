# 96-Well Plate RNA Barcode Analysis
This project provides a Tkinter GUI application for analyzing RNA barcodes from sequencing data, focusing on 96-well plates. It includes:
- Barcode reading and clustering logic.
- Visualization and reporting of results to both text and PDF files.
- Single-plate or multi-plate analyses with user-specified row/column barcodes.

## Project Structure
- barcodes/: Core logic for reading, clustering, analyzing, and processing barcodes.
- gui/: Tkinter GUI application code.
- main.py: Entry point that launches the GUI.
- requirements.txt: Lists Python package dependencies.
- README.md: Project overview and usage instructions.

## Getting Started
1. Install Dependencies
   Make sure you have Python 3 installed. Install required packages:
   pip install -r requirements.txt
   
2. Run the Application
   From the project root (my_project/), run:
   python main.py

3. Using the GUI 
   - Sequencing Data (.fastq or .txt): Select the text-based file containing your sequencing reads.
   - Row Barcodes / Column Barcodes: Provide the lists of row and column barcodes in plain text (one barcode per line).
   - Flanking Sequence 1 / 2: Enter the 5' and 3' sequences that flank the region where your barcode is located.
   - Expected RNA Barcode Length: Enter an approximate expected length of the barcode (the program automatically adds a buffer of +5 for sequence replacements).
   - Edit Tolerance: Set how many mismatches or edits (distance threshold) are tolerated when clustering barcodes.
   - Raw Data Output File (.txt): Where to save the textual summary of the results.
   - Graphical Data Output File (.pdf): Where to save the bar chart summaries.
   - Plate IDs (for multiple analysis) (Optional): If you have multiple plates in the same file, list their identifying tags (one per line). The script will split reads by plate ID into separate files and run the analysis individually for each plate.

When you click Process Barcodes, the application will:
   - Read and parse the barcodes.
   - Cluster similar barcodes (within the specified edit tolerance).
   - Output text summaries and PDF bar charts for each well (or each plate, if multi-plate analysis).