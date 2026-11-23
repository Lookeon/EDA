# %% 1. Carregar dados
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False})
Path("graficos").mkdir(exist_ok=True)

conexao = sqlite3.connect("gta.db")
df = pd.read_sql_query("SELECT * FROM gta6_final", conexao)

# flag de direcao sem veiculo (caso ainda nao exista na tabela)
df["dirigindo_sem_veiculo"] = (df["primary_action"] == "Driving") & (df["vehicle_count"] == 0)

print(df.shape)  # esperado: (500, 25)
df.head(3)

# %% 2. Funcao auxiliar de grafico de barras
def barras(col, ax=None, cor="#0f9488", ordenar=True):
    contagem = df[col].value_counts()
    if not ordenar:
        contagem = contagem.sort_index()
    ax = ax or plt.gca()
    contagem.plot.bar(ax=ax, color=cor, rot=30)
    ax.set_title(col)
    ax.set_xlabel("")
    ax.set_ylabel("frames")
    for i, v in enumerate(contagem.values):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=8)

# %% 3. Cena, ambiente, horario, clima, iluminacao, acao
cols = ["scene_type", "primary_action", "weather", "lighting_condition", "time_of_day", "environment"]
fig, axes = plt.subplots(2, 3, figsize=(16, 8))
for col, ax in zip(cols, axes.ravel()):
    barras(col, ax)
fig.suptitle("Distribuicao das variaveis categoricas (500 frames)", fontsize=14)
fig.tight_layout()
fig.savefig("graficos/01_categoricas.png")
plt.show()

# %% 4. Contagens numericas: personagens, veiculos, animais
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for col, ax in zip(["character_count", "vehicle_count", "animal_count"], axes):
    barras(col, ax, ordenar=False, cor="#6366f1")
fig.suptitle("Contagens por frame", fontsize=14)
fig.tight_layout()
fig.savefig("graficos/02_contagens.png")
plt.show()

print(df[["character_count", "vehicle_count", "animal_count"]].describe().round(2))

# %% 5. Trailers
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
barras("trailer_number", axes[0], ordenar=False)
pd.crosstab(df["trailer_number"], df["scene_type"]).T.plot.bar(ax=axes[1], rot=30)
axes[1].set_title("Cena por trailer")
pd.crosstab(df["trailer_number"], df["primary_action"]).T.plot.bar(ax=axes[2], rot=30)
axes[2].set_title("Acao por trailer")
fig.tight_layout()
fig.savefig("graficos/03_trailers.png")
plt.show()

# %% 6. Armas (somente os frames com informacao)
armas = df.loc[df["weapons_visible"] != "Não informado", "weapons_visible"].value_counts()
status = df["weapons_info_status"].value_counts()

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
armas.plot.bar(ax=axes[0], color="#e11d48", rot=0)
axes[0].set_title(f"Tipos de arma registrados (n={armas.sum()})")
for i, v in enumerate(armas.values):
    axes[0].text(i, v, str(v), ha="center", va="bottom")
status.plot.pie(ax=axes[1], autopct="%1.1f%%", colors=["#cbd5e1", "#e11d48"], ylabel="")
axes[1].set_title("Frames com e sem info de arma")
fig.tight_layout()
fig.savefig("graficos/04_armas.png")
plt.show()

# %% 7. Personagens mais frequentes (a coluna guarda varios nomes separados por ;)
personagens = (
    df["characters_present"].str.split(";").explode().str.strip().value_counts()
)
print(personagens)

plt.figure(figsize=(8, 4))
personagens.sort_values().plot.barh(color="#f59e0b")
plt.title("Aparicoes por personagem (em quantos frames aparece)")
plt.tight_layout()
plt.savefig("graficos/05_personagens.png")
plt.show()

# %% 8. Palavras-chave mais comuns
kw = df["keywords"].str.split(",").explode().str.strip().value_counts()
print(kw.head(20))

plt.figure(figsize=(8, 6))
kw.head(20).sort_values().plot.barh(color="#14b8a6")
plt.title("Top 20 keywords")
plt.tight_layout()
plt.savefig("graficos/06_keywords.png")
plt.show()

# %% 9. Mapa de calor: acao x cena
tabela = pd.crosstab(df["primary_action"], df["scene_type"])
fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(tabela.values, cmap="YlGnBu")
ax.set_xticks(range(len(tabela.columns)), tabela.columns, rotation=40, ha="right")
ax.set_yticks(range(len(tabela.index)), tabela.index)
for i in range(tabela.shape[0]):
    for j in range(tabela.shape[1]):
        ax.text(j, i, tabela.values[i, j], ha="center", va="center", fontsize=8)
ax.set_title("Acao x cena (numero de frames)")
fig.colorbar(im, ax=ax)
fig.tight_layout()
fig.savefig("graficos/07_acao_x_cena.png")
plt.show()

# %% 10. Veiculos e animais por acao
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
df.groupby("primary_action")["vehicle_count"].mean().sort_values().plot.barh(ax=axes[0], color="#6366f1")
axes[0].set_title("Media de veiculos por frame, por acao")
df.groupby("scene_type")["animal_count"].mean().sort_values().plot.barh(ax=axes[1], color="#84cc16")
axes[1].set_title("Media de animais por frame, por cena")
fig.tight_layout()
fig.savefig("graficos/08_medias.png")
plt.show()

# %% 11. Tabela-resumo de qualidade do dataset
resumo = pd.DataFrame(
    [
        ["Linhas originais", 10000, "Dataset bruto"],
        ["Linhas duplicadas removidas", 9500, "20 copias de cada frame; ficaram 500 unicos"],
        ["weapons_visible NULL", int((df["weapons_info_status"] == "Não informado").sum()), "Preenchido com 'Não informado' + flag"],
        ["Tiro sem arma registrada", int(df["tiro_sem_arma_registrada"].sum()), "Inconsistencia sinalizada"],
        ["Direcao sem veiculo", int(df["dirigindo_sem_veiculo"].sum()), "Inconsistencia sinalizada"],
        ["animals_present NULL", int((df["animals_present"] == "Nenhum").sum()), "Contagem = 0, preenchido com 'Nenhum'"],
        ["vehicles_present NULL", int((df["vehicles_present"] == "Nenhum").sum()), "Contagem = 0, preenchido com 'Nenhum'"],
        ["Nulos restantes", int(df.isna().sum().sum()), "Nenhum"],
    ],
    columns=["Item", "Frames/linhas", "Tratamento"],
)
resumo

# %% [markdown]
# ## Conclusoes
# - O dataset original tinha 95% de linhas duplicadas (20 copias de cada frame). Apos remover, ficaram 500 frames.
# - Cena, acao, clima, iluminacao e armas estao quase uniformemente distribuidos.
# - O NULL de `weapons_visible` (61,8%) nao significa "sem arma": 35 frames de tiro estao sem arma registrada.
# - Ambiente x cena e horario x iluminacao nao tem associacao estatistica (p > 0,4):
#   as colunas parecem geradas de forma independente, o que e tipico de dados sinteticos.
# - Limitacao: por isso, conclusoes do tipo "cena X tem mais Y" nao se sustentam.
#   O valor do projeto esta no processo de limpeza e validacao.
# %%
