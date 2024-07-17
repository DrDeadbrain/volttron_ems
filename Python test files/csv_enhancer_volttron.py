import csv

def add_metadata_to_csv(input_file, output_file, unit):
    # Die CSV-Datei einlesen
    with open(input_file, mode='r', newline='') as infile:
        reader = csv.reader(infile)
        rows = list(reader)  # Alle Zeilen in einer Liste speichern

    # Neue erste Zeile hinzufügen
    header = ["Point Name", "Volttron Point Name", "Units", "Writable", "Default Value", "Type"]

    # Neue Werte hinzufügen und in eine neue Datei schreiben
    with open(output_file, mode='w', newline='') as outfile:
        writer = csv.writer(outfile)
        
        # Header-Zeile schreiben
        writer.writerow(header)
        
        
        # Generiere den Punktnamen 
        point_name = f"Building1_Pel"

        for i, row in enumerate(rows, start=1):
            
            # Generiere den Punktnamen 
            point_name = f"Building2_Pel{i}"
            # Nehme an, dass der Energieverbrauchswert das erste Feld in jeder Zeile ist
            energy_value = row[1]  # oder entsprechend dem Index des Energieverbrauchswerts
            
            # Die neuen Werte am Anfang der Zeile hinzufügen
            new_row = [point_name, point_name, unit, "FALSE", energy_value, "Type"] + row
            writer.writerow(new_row)

# Beispielnutzung des Skripts
input_file = 'TEC_PEL_1W.csv'  # Name der Eingabedatei
output_file = 'TEC_PEL_2W.csv'  # Name der Ausgabedatei
unit = 'kW'  # Definierbare Einheit für den Wert
writable = False  # Beschreibbar (True oder False)

add_metadata_to_csv(input_file, output_file, unit)

#metadata must match
#csv naming must be dynamic for every possible csv
