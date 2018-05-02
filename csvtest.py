import csv

with open('tracks/exported_tracks.txt','rb') as f:
    reader = csv.reader(f, delimiter = '\t' )
    row_count = sum(1 for i in reader)

    for row in range(row_count):
        print(reader.row[1])
