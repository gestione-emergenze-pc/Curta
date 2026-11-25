# Prova: se il sito della Regione non funziona il monitor non scrive su Telegram; gli altri errori si segnalano al 3° controllo di fila.
# Esecuzione: python3 prove/monitor_sito_giu_test.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "monitor-allerte"))
import requests
import monitor_allerte as m

fail = 0
def ok(c, t):
    global fail
    print(("OK   " if c else "FALLITA ") + t)
    if not c: fail = 1

class Arch:
    def __init__(self): self.d = {}
    def leggi(self, k): return self.d.get(k)
    def scrivi(self, k, v): self.d.setdefault(k, {}).update(v)

def risposta(codice):
    r = requests.Response(); r.status_code = codice; return r

def giro(errore, prima=2):
    A = Arch(); A.scrivi("cfd_stato/monitor", {"erroriConsecutivi": prima}); inviati = []
    def falso(*a, **k): raise errore
    m.http_get = falso
    rc = m.esegui(A, lambda t: inviati.append(t) or True)
    return rc, inviati, A

for nome, e in [("connessione rifiutata", requests.exceptions.ConnectionError("x")),
                ("tempo scaduto", requests.exceptions.ConnectTimeout("x")),
                ("errore 503 del sito", requests.exceptions.HTTPError("503", response=risposta(503)))]:
    rc, inv, A = giro(e)
    ok(inv == [] and A.d["cfd_stato/monitor"]["erroriConsecutivi"] == 3, f"{nome}: nessun messaggio al 3 controllo di fila, contatore aggiornato")

for nome, e in [("pagina cambiata", RuntimeError("nessun documento di allerta trovato")),
                ("403 (accesso negato)", requests.exceptions.HTTPError("403", response=risposta(403))),
                ("404", requests.exceptions.HTTPError("404", response=risposta(404)))]:
    rc, inv, A = giro(e)
    ok(len(inv) == 1 and "3 controlli consecutivi falliti" in inv[0], f"{nome}: il messaggio parte come prima")
sys.exit(fail)
