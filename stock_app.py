'''
Proiectul este o aplicatie creata pentru a tine gestiunea stocurilor unui depozit

Se creaza o clasa 'Stoc' care va avea:
  - o metoda constructor cu
        - denumire produs
        - categoria
        - unitatea de masura default 'Kg'
        - sold default 0
        - se initializeaza un dictionar {1: [data, cant_intrata, cant_iesita]}

  - o metoda intrari cu
        - cantitatea
        - data = str ( datetime.now ( ).strftime ( '%Y%m%d' ) )
        - se testeaza daca exista chei in dictionarul cu data op
        - se introduce in dict intrari cheia si cantitatea
        - se introduce in dict data cheie si data op
        - se actualizeaza soldul

  - o metoda iesiri, similara cu precedenta. Diferente: se populeaza dict iesiri

  - o metoda fisa produsului cu urmatoarele specificatii:
        - Sa printeze 'Fisa produsului "denumire_produs", UM' (pentru a sti a cui este fisa)
        - Sa printeze ' Nrc ', '  Data  ', ' Intrare', ' Iesire' pentru toate tranzactiile produsului
        - Sa printeze stocul actual al produsului

  - implementam o solutie care sa returneze o proiectie grafica a intrarilor si iesirilor intr-o
    anumita perioada, pentru un anumit produs;	--pygal--

  - implementam o metoda cu ajutorul careia se vor transmite prin email diferite informatii
    (de exemplu fisa produsului) ; 	--SMTP--

  - implementam o solutie care sa avertizeze automat cand stocul unui produs este mai mic decat o
    limita minima, predefinita per produs. Limita sa poata fi variabila (per produs). Aceasta metoda
    transmite automat un email de avertizare

  - se creaza o baza de date --sqlite3-- care sa cuprinda urmatoarele tabele:
    Categoria
        - idc INT NOT NULL AUTO_INCREMENT PRIMARY KEY
        - denc VARCHAR(255)
    Produs
        - idp INT NOT NULL AUTO_INCREMENT PRIMARY KEY
        - idc INT NOT NULL
        - denp VARCHAR(255)
        - pret DECIMAL(8,2) DEFAULT 0
        # FOREIGN KEY (idc) REFERENCES Categoria.idc ON UPDATE CASCADE ON DELETE RESTRICT
    Operatiuni
        - ido INT NOT NULL AUTO_INCREMENT PRIMARY KEY
        - idp INT NOT NULL
        - cant DECIMAL(10,3) DEFAULT 0
        - data DATE

  - Completam aplicatia astfel incat sa permita introducerea pretului la fiecare intrare si iesire.
    Pretul de iesire va fi pretul mediu ponderat (la fiecare tranzactie de intrare se va face o medie
    intre pretul produselor din stoc si al celor intrate ceea ce va deveni noul pret al produselor stocate).
    Pretul de iesire va fi pretul din acel moment.

'''

import datetime
import sqlite3
from sqlite3 import Error
import pygal
import smtplib
from email.message import EmailMessage


class Stoc:
    """Tine stocul unui depozit"""
    tot_categ = 0
    tot_prod = 0
    categorii = list()
    produse = list()
    categ_prod = {}
    pret = 0

    def __init__(self, prod, categ, um='Buc', sold=0, limita=30):
        self.prod = prod  # parametri cu valori default ii lasam la sfarsitul listei
        self.categ = categ  # fiecare instanta va fi creata obligatoriu cu primii trei param.
        self.sold = sold  # al patrulea e optional, soldul va fi zero
        self.um = um
        self.i = {}  # fiecare instanta va avea trei dictionare intrari, iesiri, data
        self.e = {}  # pentru mentinerea corelatiilor cheia operatiunii va fi unica
        self.d = {}

        Stoc.tot_prod += 1  # la fiecare instantiere se calculeaza numarul produselor si al categ
        Stoc.produse.append(prod)  # populam lista cu produse

        if categ not in Stoc.categorii:  # populam lista cu categorii, daca nu exista (unicitate)
            Stoc.tot_categ += 1
            Stoc.categorii.append(categ)
            Stoc.categ_prod[categ] = {prod}
        else:
            Stoc.categ_prod[categ].add(prod)
        self.limita = limita

    def intr(self, cant, data=str(datetime.datetime.now().strftime('%Y%m%d')), pret_cant=0):
        if self.sold == 0:
            Stoc.pret = pret_cant
        else:
            medie = (self.sold * Stoc.pret + cant * pret_cant) / (self.sold + cant)
            Stoc.pret = medie
        self.sold += cant  # recalculam soldul dupa fiecare tranzactie
        if self.d.keys():  # dictionarul data are toate cheile (fiecare tranzactie are data)
            cheie = max(self.d.keys()) + 1
        else:
            cheie = 1
        self.i[cheie] = cant  # introducem valorile in dictionarele de intrari si data
        self.d[cheie] = data

    def iesi(self, cant, data=str(datetime.datetime.now().strftime('%Y%m%d'))):
        if self.sold <= self.limita:
            self.send_mail("Articolul dorit nu se afla in cantitate suficienta in Stocul magazinului.")
            #print("Cantitate insuficienta")
            return 0

        pret_profit = self.pret * cant
        self.sold -= cant
        if self.d.keys():
            cheie = max(self.d.keys()) + 1
        else:
            cheie = 1
        self.e[cheie] = cant  # similar, introducem datele in dictionarele iesiri si data
        self.d[cheie] = data
        return pret_profit

    def fisap(self):
        print('Fisa produsului ' + self.prod + ': ' + self.um)
        print('----------------------------')
        print(' Nrc ', '  Data ', 'Intrari', 'Iesiri')
        print('----------------------------')
        for v in self.d.keys():
            if v in self.i.keys():
                print(str(v).rjust(5), self.d[v], str(self.i[v]).rjust(6), str(0).rjust(6))
            else:
                print(str(v).rjust(5), self.d[v], str(0).rjust(6), str(self.e[v]).rjust(6))
        print('----------------------------')
        print('Stoc actual       ' + str(self.sold).rjust(10))
        print('----------------------------\n')

    def fisap_to_string(self):
        fisap_str = ''
        fisap_str += 'Fisa produsului ' + self.prod + ': ' + self.um + '\n'
        fisap_str += '--------------------------------' + '\n'
        fisap_str += ' Nrc ' + '  Data ' + ' Intrari ' + ' Iesiri' + '\n'
        fisap_str += '--------------------------------' + '\n'
        for v in self.d.keys():
            if v in self.i.keys():
                fisap_str += str(v).rjust(5) + " " + str(self.d[v]) + str(self.i[v]).rjust(6) + str(0).rjust(6) + '\n'
            else:
                fisap_str += str(v).rjust(5) + " " + str(self.d[v]) + str(0).rjust(6) + str(self.e[v]).rjust(6) + '\n'
        fisap_str += '--------------------------------' + '\n'
        fisap_str += 'Stoc actual       ' + str(self.sold).rjust(10) + '\n'
        fisap_str += '--------------------------------\n'
        return fisap_str

    def grafic(self, stoc_produs, data):
        dict_intrari = {}
        dict_iesiri = {}
        print(stoc_produs.d)
        print(stoc_produs.i)
        print(stoc_produs.e)
        for v in stoc_produs.d.keys():
            if v in stoc_produs.i.keys():
                if stoc_produs.d[v] not in dict_intrari:
                    dict_intrari[stoc_produs.d[v]] = stoc_produs.i[v]
                else:
                    dict_intrari[stoc_produs.d[v]] += stoc_produs.i[v]

            elif v in stoc_produs.e.keys():
                if stoc_produs.d[v] not in dict_iesiri:
                    dict_iesiri[stoc_produs.d[v]] = stoc_produs.e[v]
                else:
                    dict_iesiri[stoc_produs.d[v]] += stoc_produs.e[v]

        ob_c1 = pygal.StackedLine(title='Operatiuni Stoc',
                                  x_title='Data',
                                  y_title='Nr. Operatiuni',
                                  title_font_size=25)
        ob_c1.add('intrari', dict_intrari.values())
        ob_c1.add('iesiri', dict_iesiri.values())
        ob_c1.x_labels = dict_intrari.keys()
        ob_c1.render_to_file('catalog.svg')

    def create_connection(self, db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)

        return conn

    def create_table(self, conn, create_table_sql):
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def insert_row(self, conn, insert_row_sql):
        try:
            c = conn.cursor()
            c.execute(insert_row_sql)
            print(c.lastrowid)
            # conn.commit()
        except Error as e:
            print(e)

    def print_table(self, conn, table_name):
        try:
            c = conn.cursor()
            c.execute(f"SELECT * from {table_name}")
            rows = c.fetchall()
            print(rows)

        except Error as e:
            print(e)

    def main(self):
        database = r"C:\sqlite\pythonsqlite.db"

        sql_create_Categorie_table = """ CREATE TABLE IF NOT EXISTS Categorie (idc INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                            denc text(255));"""

        sql_create_Produs_table = """CREATE TABLE IF NOT EXISTS Produs (idp INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                        idc INTEGER NOT NULL,
                                        denp text(255),
                                        pret DECIMAL(8,2) DEFAULT 0,
                                        FOREIGN KEY (idc) REFERENCES Categorie ON UPDATE CASCADE ON DELETE RESTRICT);"""

        sql_create_Operatiuni_table = """ CREATE TABLE IF NOT EXISTS Operatiuni (ido INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                                idp INTEGER NOT NULL,
                                                cant DECIMAL(10,3) DEFAULT 0,
                                                data DATE);"""
        sql_insert_in_Categorie = '''INSERT INTO Categorie
                 VALUES(1, 'fragute')'''

        conn = self.create_connection(database)

        if conn is not None:
            self.create_table(conn, sql_create_Categorie_table)
            self.create_table(conn, sql_create_Produs_table)
            self.create_table(conn, sql_create_Operatiuni_table)

            self.insert_row(conn, sql_insert_in_Categorie)
            self.print_table(conn, 'Categorie')
            # conn.close()
        else:
            print("Error! cannot create the database connection.")

    # if __name__ == '__main__':
    #     main()

    def send_mail(self, content):
        self.msg = EmailMessage()
        self.msg['Subject'] = 'Proiect Python'
        self.msg['From'] = 'exemplu@gmail.com'
        self.msg['To'] = 'exemplu@gmail.com'
        self.msg.set_content(content)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('exemplu@gmail.com', 'parola')

            smtp.send_message(self.msg)

fragute = Stoc('fragute', 'fructe', 'kg')
data = datetime.date.today() + datetime.timedelta(days=1)
data = str(data.strftime('%Y%m%d'))
fragute.intr(100, data=datetime.date.today(), pret_cant=5)
fragute.intr(100, data=datetime.date.today() + datetime.timedelta(days=2), pret_cant=10)
fragute.iesi(20, data=datetime.date.today())
fragute.iesi(15, data=datetime.date.today() + datetime.timedelta(days=2))


#fragute.fisap_to_string()
#fragute.send_mail(fragute.fisap_to_string())
#fragute.main()
#fragute.grafic(fragute, data)

