ff = open('openings_html.txt','r')
lines = ff.readlines()
ff.close()
eco_code = '0'
opening_name = ''
opening_line = ''
ff = open('eco_codes.txt','w')
for line in lines:
    if "<font face='arial,helvetica'>" in line:
        eco_code = line.split("<font face='arial,helvetica'>")[1].split("<")[0]
        opening_name = line.split("<font face='arial,helvetica'><B>")[1].split("<")[0]
        #print(eco_code)
    if "<font size=-1>" in line:
        opening_line = line.split("<font size=-1>")[1].split("<")[0]
        print(eco_code, opening_name, opening_line)
    ff.write(eco_code + "|" + opening_name + "|" + opening_line + "\n")
ff.close()