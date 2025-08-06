# simulate_random_walk.py
import numpy as np
import matplotlib.pyplot as plt

# Parametry simulace
n_days = 100  # počet dní
start_price = 100  # počáteční cena
volatility = 1  # velikost náhodného pohybu

# Inicializace pole pro cenu
prices = [start_price]

# Simulace náhodného pohybu
for _ in range(n_days):
    shock = np.random.normal(0, volatility)
    new_price = prices[-1] + shock
    prices.append(new_price)

# Graf výsledků
plt.plot(prices)
plt.title("Simulace vývoje ceny akcie")
plt.xlabel("Den")
plt.ylabel("Cena")
plt.grid(True)
plt.show()
