"""Dati per il grafico dei set vinti per partita (SVG disegnato nel template)."""
import datetime

SLOTS = 14      # partite previste dal calendario (asse orizzontale)
YMAX = 20       # set totali in una partita (asse verticale)
W, H = 720, 320
LEFT, RIGHT, TOP, BOTTOM = 56, 24, 34, 58


def build_chart(games):
    """Costruisce il grafico dai risultati della nostra squadra.

    `games` è una lista di dict con id, date, won, lost, opponent (in qualsiasi ordine):
    le partite vengono messe in ordine cronologico e numerate 1, 2, 3...
    Tutti i numeri sono interi, così nel template non compaiono virgole decimali.
    Se non ci sono partite restituisce None.
    """
    if not games:
        return None
    games = sorted(games, key=lambda g: (g["date"] or datetime.date.min, g["id"]))

    slots = max(SLOTS, len(games))
    plot_w = W - LEFT - RIGHT
    plot_h = H - TOP - BOTTOM
    bottom = TOP + plot_h

    def x(i):
        return round(LEFT + (i - 0.5) * plot_w / slots)

    def y(v):
        return round(TOP + plot_h * (1 - min(max(v, 0), YMAX) / YMAX))

    dots = [
        {
            "id": g["id"],
            "cx": x(i),
            "cy": y(g["won"]),
            "title": f"Partita {i}: contro {g['opponent']}, {g['won']}-{g['lost']}",
        }
        for i, g in enumerate(games, 1)
    ]
    return {
        "width": W,
        "height": H,
        "left": LEFT,
        "right": W - RIGHT,
        "top": TOP,
        "bottom": bottom,
        "yticks": [{"y": y(v), "tx": LEFT - 10, "value": v} for v in range(0, YMAX + 1, 2)],
        "xticks": [{"x": x(i), "y": bottom + 22, "value": i} for i in range(1, slots + 1)],
        "xtitle_x": round(LEFT + plot_w / 2),
        "xtitle_y": H - 10,
        "ytitle_x": 16,
        "ytitle_y": round(TOP + plot_h / 2),
        "tie_y": y(10),
        "tie_label_y": y(10) - 7,
        "line": " ".join(f"{d['cx']},{d['cy']}" for d in dots),
        "dots": dots,
    }
