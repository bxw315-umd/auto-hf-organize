Datasets should be in huggingface format, with one row per sample.
Voltammograms will have potential and current data. The column names will be `potential` and `current` respectively.
Concentrations will be floats. Concentration column names will contain molecule names only in the same lower case convention as python(e.g. ai-1 concentration -> `ai1`).

It may be the case that this dataset comes from a CHI potentiostat.
Raw data files from a CHI potentiostat are often in both .bin and .txt formats. The .bin formats are not readable, so use the .txt only.
.txt files can be parsed using chi_txt_parser.py.

