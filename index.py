import json
import hashlib
import csv
import datetime
import matplotlib.pyplot as plt

# Step 1: Read JSON file and parse data
with open('data.json') as f:
    data = json.load(f)

# Step 1a: Select required columns and transform data
processed_data = []
for entry in data:
    processed_entry = {
        'appointmentId': entry['appointmentId'],
        'phoneNumber': entry['phoneNumber'],
        'firstName': entry['patientDetails']['firstName'],
        'lastName': entry['patientDetails']['lastName'],
        'gender': 'male' if entry['patientDetails']['gender'] == 'M' else 'female' if entry['patientDetails']['gender'] == 'F' else 'others',
        'DOB': entry['patientDetails']['birthDate'],
        'medicines': entry['consultationData']['medicines']
    }
    processed_data.append(processed_entry)

# Step 1b: Create derived column fullName
for entry in processed_data:
    entry['fullName'] = entry['firstName'] + ' ' + entry['lastName']

# Step 1c: Add column isValidMobile
def is_valid_mobile(phone):
    if phone.startswith('+91') or phone.startswith('91'):
        phone = phone[-10:]  # Trim prefix
        if len(phone) == 10 and phone.isnumeric():
            return True
    return False

for entry in processed_data:
    entry['isValidMobile'] = is_valid_mobile(entry['phoneNumber'])

# Step 1d: Add column phoneNumberHash
for entry in processed_data:
    if entry['isValidMobile']:
        entry['phoneNumberHash'] = hashlib.sha256(entry['phoneNumber'].encode()).hexdigest()
    else:
        entry['phoneNumberHash'] = None

# Step 1e: Add column Age
def calculate_age(dob):
    if dob:
        dob = datetime.datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return None

for entry in processed_data:
    entry['Age'] = calculate_age(entry['DOB'])

# Step 1f: Add aggregated columns
aggregated_data = {}
for entry in processed_data:
    if entry['appointmentId'] not in aggregated_data:
        aggregated_data[entry['appointmentId']] = {
            'noOfMedicines': 0,
            'noOfActiveMedicines': 0,
            'noOfInActiveMedicines': 0,
            'medicineNames': []
        }
    aggregated_data[entry['appointmentId']]['noOfMedicines'] += len(entry['medicines'])
    for medicine in entry['medicines']:
        aggregated_data[entry['appointmentId']]['medicineNames'].append(medicine['name'])
        if medicine['IsActive']:
            aggregated_data[entry['appointmentId']]['noOfActiveMedicines'] += 1
        else:
            aggregated_data[entry['appointmentId']]['noOfInActiveMedicines'] += 1

# Step 1g: Create final dataframe
final_dataframe = []
for entry in processed_data:
    if entry['appointmentId'] in aggregated_data:
        entry.update(aggregated_data[entry['appointmentId']])
        entry['medicineNames'] = ', '.join(entry['medicineNames'])
        final_dataframe.append(entry)

# Step 2: Export final dataframe to CSV
with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[
        'appointmentId', 'fullName', 'phoneNumber', 'isValidMobile',
        'phoneNumberHash', 'gender', 'DOB', 'Age',
        'noOfMedicines', 'noOfActiveMedicines', 'noOfInActiveMedicines',
        'medicineNames'
    ], delimiter='~')
    writer.writeheader()
    writer.writerows(final_dataframe)

# Step 2h: Export aggregated data to JSON
aggregated_json = {
    'Age': sum(entry['Age'] for entry in final_dataframe if entry['Age'] is not None) / len(final_dataframe),
    'gender': {
        'male': sum(1 for entry in final_dataframe if entry['gender'] == 'male'),
        'female': sum(1 for entry in final_dataframe if entry['gender'] == 'female'),
        'others': sum(1 for entry in final_dataframe if entry['gender'] == 'others')
    },
    'validPhoneNumbers': sum(1 for entry in final_dataframe if entry['isValidMobile']),
    'appointments': len(final_dataframe),
    'medicines': sum(entry['noOfMedicines'] for entry in final_dataframe),
    'activeMedicines': sum(entry['noOfActiveMedicines'] for entry in final_dataframe)
}

with open('aggregated_data.json', 'w') as jsonfile:
    json.dump(aggregated_json, jsonfile, indent=4)

# Step 2h-2: Plot pie chart
gender_counts = [aggregated_json['gender']['male'], aggregated_json['gender']['female'], aggregated_json['gender']['others']]
labels = ['Male', 'Female', 'Others']
plt.pie(gender_counts, labels=labels, autopct='%1.1f%%')
plt.title('Appointments by Gender')
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
plt.savefig('gender_pie_chart.png')  # Save the plot as a PNG file
plt.show()
