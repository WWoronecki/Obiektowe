#importujemy potrzebne biblioteki
import tkinter as tk  #GUI – tworzenie okienek i widżetów
from PIL import Image, ImageTk  #Image – obsługa obrazów, ImageTk – konwersja do formatu Tkintera
import requests  #do pobierania danych z internetu (API NASA)
import io  #do obsługi bajtów (obraz z internetu jako strumień bajtów)
import threading  #aby pobieranie obrazów działało w tle, nie blokując GUI

#klasa aplikacji
class NasaApp:
    def __init__(self, root):  #konstruktor aplikacji, przyjmuje główne okno tkintera
        self.root = root  #przechowujemy referencję do głównego okna
        self.root.title("NASA Image Search")  #ustawiamy tytuł okna
        self.root.configure(bg="black")  #ustawiamy kolor tła na czarny
        self.root.geometry('1920x1080')  #ustawiamy rozmiar okna

        self.setup_widgets()  #wywołanie metody tworzącej wszystkie elementy GUI
        self.images = []  #lista referencji do obrazów, by nie zostały usunięte przez garbage collector

    def setup_widgets(self):  #metoda tworząca GUI i rozmieszczająca widżety
        self.exit_button = tk.Button(self.root, text="X", bg="white", fg="green", width=5, command=self.close)
        #przycisk wyjścia, biały z zieloną czcionką, wywołuje zamknięcie aplikacji
        self.exit_button.grid(row=0, column=2, sticky="ne")  #pozycjonowanie w prawym górnym rogu

        self.query_label = tk.Label(self.root, text="Podaj zapytanie:", bg="black", fg="green", font=("Arial", 14))
        #etykieta informująca użytkownika o polu wyszukiwania
        self.query_label.grid(row=0, column=0, columnspan=3, padx=6, pady=6, sticky="n")
        #rozciągnięcie na 3 kolumny, trochę odstępu i wyrównanie do góry

        self.query_entry = tk.Entry(root, width=100, bg="black", fg="lime", insertbackground="lime")
        #pole tekstowe do wpisania zapytania, czarne tło, zielony tekst i kursor
        self.query_entry.grid(row=1, column=1, sticky="we")  #środkowa kolumna, rozciąga się poziomo

        self.search_button = tk.Button(root, text="Szukaj", command=self.search_images, bg="black", fg="lime")
        #przycisk wywołujący wyszukiwanie obrazów, wywołuje metodę search_images
        self.search_button.grid(row=1, column=2, sticky="w", padx=2)  #obok pola tekstowego

        self.console_frame = tk.Frame(self.root, bg="black")  #ramka na konsolę (tekst logów)
        self.console_frame.grid(row=2, column=2, sticky="nse", pady=10, padx=10)

        self.image_container = tk.Frame(root, bg="black")  #ramka na miniaturki obrazów
        self.image_container.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.canvas = tk.Canvas(self.image_container, bg="black", highlightthickness=0)
        #płótno do przewijania zawartości (obrazków)
        self.scrollbar = tk.Scrollbar(self.image_container, orient="vertical", command=self.canvas.yview)
        #pionowy pasek przewijania powiązany z płótnem
        self.scrollable_frame = tk.Frame(self.canvas, bg="black")  #wewnętrzna ramka na obrazy

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        #automatyczne dopasowanie rozmiaru przewijanego obszaru do zawartości
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        #dodanie scrollowalnej ramki do płótna
        self.canvas.configure(yscrollcommand=self.scrollbar.set)  #powiązanie paska z canvasem

        self.canvas.pack(side="left", fill="both", expand=True)  #płótno zajmuje lewą stronę ramki
        self.scrollbar.pack(side="right", fill="y")  #scrollbar po prawej stronie

        self.console_label = tk.Label(self.console_frame, text="Konsola", bg="black", fg="lime", font=("Arial", 16))
        #nagłówek konsoli
        self.console_label.pack(anchor="w", padx=5, pady=(0, 5))  #przesunięcie w lewo

        self.console = tk.Text(self.console_frame, height=8, bg="black", fg="lime", state="disabled", font=("Arial", 16))
        #tekstowe pole do wypisywania komunikatów, tylko do odczytu
        self.console.pack(fill="both", expand='true')  #rozciąga się w ramce

        self.root.grid_rowconfigure(1, weight=0)  #drugi wiersz bez rozciągania
        self.root.grid_rowconfigure(2, weight=1)  #trzeci wiersz ma się rozciągać
        self.root.grid_columnconfigure(0, weight=1, uniform="a")  #wszystkie kolumny mają równy rozmiar
        self.root.grid_columnconfigure(1, weight=1, uniform="a")
        self.root.grid_columnconfigure(2, weight=1, uniform="a")

    def log(self, message):  #metoda wypisująca komunikaty do konsoli
        self.console.config(state="normal")  #odblokowanie pola
        self.console.insert("end", message + "\n")  #dodanie tekstu
        self.console.see("end")  #automatyczne przewinięcie w dół
        self.console.config(state="disabled")  #ponowne zablokowanie edycji

    def search_images(self):  #metoda rozpoczynająca wyszukiwanie obrazów
        query = self.query_entry.get().strip()  #pobranie zapytania i usunięcie spacji
        if not query:  #jeśli nic nie wpisano
            self.log("Wpisz zapytanie!")  #komunikat o błędzie
            return

        self.log(f"Szukanie: {query}")  #wypisanie zapytania
        self.clear_images()  #usunięcie poprzednich wyników

        def run():  #funkcja działająca w osobnym wątku
            try:
                response = requests.get("https://images-api.nasa.gov/search", params={"q": query, "media_type": "image"})
                #wysłanie zapytania GET do API NASA z parametrem wyszukiwania
                response.raise_for_status()  #błąd jeśli odpowiedź nie była poprawna
                items = response.json().get("collection", {}).get("items", [])[:15]
                #pobranie maksymalnie 15 wyników obrazów

                if not items:  #jeśli nie znaleziono wyników
                    self.log("Brak wyników.")
                    return

                for item in items:  #dla każdego wyniku
                    title = item["data"][0]["title"]  #tytuł obrazka
                    img_url = item["links"][0]["href"]  #adres obrazka
                    self.root.after(0, lambda t=title, u=img_url: self.display_image(t, u))
                    #wywołanie wyświetlania obrazka w GUI (w głównym wątku)

            except Exception as e:
                self.log(f" Błąd: {e}")  #obsługa błędów

        threading.Thread(target=run).start()  #uruchomienie funkcji w osobnym wątku

    def display_image(self, title, url):  #metoda do wyświetlania miniaturki i tytułu
        try:
            img_data = requests.get(url).content  #pobranie danych obrazka
            img = Image.open(io.BytesIO(img_data))  #otwarcie jako obraz
            img.thumbnail((250, 250))  #zmniejszenie do miniaturki
            photo = ImageTk.PhotoImage(img)  #konwersja do formatu tkinter
            self.images.append(photo)  #zapisanie referencji (aby obraz nie zniknął)

            col_count = 3  #liczba kolumn w siatce
            index = len(self.images) - 1  #indeks obecnego obrazka
            row = index // col_count  #obliczenie wiersza
            col = index % col_count  #obliczenie kolumny

            frame = tk.Frame(self.scrollable_frame, bg="black")  #ramka na miniaturkę i tytuł
            frame.grid(row=row, column=col, padx=10, pady=10)  #umieszczenie w siatce

            label = tk.Label(frame, image=photo, bg="black", cursor="hand2")  #obrazek z kursorem kliknięcia
            label.pack()  #dodanie do ramki
            label.bind("<Button-1>", lambda e: self.open_full_image(title, url))  #kliknięcie otwiera pełny obraz

            text = tk.Label(frame, text=title, wraplength=180, bg="black", fg="lime", font=("Arial", 12))
            #podpis pod miniaturką
            text.pack()  #dodanie podpisu do ramki

        except Exception as e:
            self.log(f" Nie udało się załadować obrazka: {e}")  #obsługa błędów

    def open_full_image(self, title, url):  #otwieranie pełnego obrazu w nowym oknie
        try:
            full_image_window = tk.Toplevel(self.root)  #nowe okno potomne
            full_image_window.title(title)  #tytuł okna = tytuł obrazka
            full_image_window.configure(bg="black")  #czarne tło

            frame = tk.Frame(full_image_window, bg="black")  #główna ramka
            frame.pack(fill="both", expand=True)

            close_button = tk.Button(frame, text="X", command=full_image_window.destroy, bg="white", fg="green", width=5)
            #przycisk zamykający okno
            close_button.pack(anchor="ne", padx=5, pady=5)

            img_data = requests.get(url).content  #pobranie pełnego obrazka
            image = Image.open(io.BytesIO(img_data))  #konwersja do obrazu
            photo = ImageTk.PhotoImage(image)  #konwersja do tkintera

            img_label = tk.Label(frame, image=photo, bg="black")  #etykieta z obrazkiem
            img_label.image = photo  #zachowanie referencji
            img_label.pack()

        except Exception as e:
            self.log(f" Błąd podczas otwierania pełnego obrazu: {e}")  #log błędu

    def clear_images(self):  #czyszczenie poprzednich wyników
        for widget in self.scrollable_frame.winfo_children():  #dla każdego widżetu w ramce
            widget.destroy()  #usuń go
        self.images.clear()  #czyść listę referencji do obrazków

    def close(self):  #zamykanie aplikacji
        self.root.destroy()  #zniszczenie głównego okna

#uruchomienie aplikacji
if __name__ == "__main__":  #blok główny
    root = tk.Tk()  #tworzenie głównego okna
    app = NasaApp(root)  #tworzenie instancji aplikacji
    root.mainloop()  #uruchomienie pętli GUI
