import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(page_title="Estatísticas Ao Vivo", layout="wide")

# ======================
# Estado da Sessão
# ======================
if 'players' not in st.session_state:
    st.session_state.players = pd.DataFrame()
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0
if 'score' not in st.session_state:
    st.session_state.score = {"Nossa":0, "Adversário":0}
if 'part' not in st.session_state:
    st.session_state.part = 1
if 'num_titulares' not in st.session_state:
    st.session_state.num_titulares = 5
if 'game_info_set' not in st.session_state:
    st.session_state.game_info_set = False
if 'modalidade' not in st.session_state:
    st.session_state.modalidade = ''
if 'tempo_parte' not in st.session_state:
    st.session_state.tempo_parte = 45
if 'clube_adversario' not in st.session_state:
    st.session_state.clube_adversario = ''
if 'playing_home' not in st.session_state:
    st.session_state.playing_home = True
if 'team_name' not in st.session_state:
    st.session_state.team_name = ''
if 'faltas_nossa' not in st.session_state:
    st.session_state.faltas_nossa = 0
if 'faltas_adversario' not in st.session_state:
    st.session_state.faltas_adversario = 0
if 'page' not in st.session_state:
    st.session_state.page = 1  # Página 1 = configuração, 2 = titulares, 3 = jogo

equipas_path = os.path.join(os.path.dirname(__file__), "Equipas")
team_files = [f for f in os.listdir(equipas_path) if f.endswith('.txt')]


# Mapear ficheiros para nomes
team_names_map = {
    "condeixa.txt": "Condeixa",
    "santaclara.txt": "Santa Clara"
}

# Carregar jogadores
def load_players(team_file):
    filepath = os.path.join(equipas_path, team_file)
    players_list = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) == 2:
                number, name = parts
                players_list.append({
                    'Número': number,
                    'Jogador': name,
                    'Em jogo': False,
                    'Golos':0, 'Assistências':0, 'Perdas de Bola':0, 'Recuperações':0,
                    'Amarelos':0,'Vermelhos':0,'Remates à Baliza':0,'Remates Fora':0,
                    'Faltas Cometidas':0,'Faltas Sofridas':0,'Defesas':0,
                    'Tempo de Jogo':0
                })
    st.session_state.players = pd.DataFrame(players_list)


# ======================
# Funções
# ======================
def add_stat(idx, stat, value=1):
    st.session_state.players.at[idx, stat] += value
    if stat == 'Golos':
        st.session_state.score['Nossa'] += value
        if st.session_state.score['Nossa'] < 0:
            st.session_state.score['Nossa'] = 0
    if stat == 'Faltas Cometidas':
        if st.session_state.playing_home:
            st.session_state.faltas_nossa += value
        else:
            st.session_state.faltas_adversario += value
    if stat == 'Faltas Sofridas':
        if st.session_state.playing_home:
            st.session_state.faltas_adversario += value
        else:
            st.session_state.faltas_nossa += value

def substitute_player(idx_out, idx_in):
    st.session_state.players.at[idx_out, 'Em jogo'] = False
    st.session_state.players.at[idx_in, 'Em jogo'] = True

def update_time():
    if st.session_state.game_started and st.session_state.start_time is not None:
        current_elapsed = time.time() - st.session_state.start_time
        delta = current_elapsed - st.session_state.elapsed_time
        st.session_state.elapsed_time = current_elapsed
        for idx, row in st.session_state.players.iterrows():
            if row['Em jogo']:
                st.session_state.players.at[idx, 'Tempo de Jogo'] += delta / 60

# ======================
# Página 1 - Configuração
# ======================
if st.session_state.page == 1:
    st.title("⚽ Configuração do Jogo")
    modalidade = st.selectbox("Selecione a modalidade:", ["Futebol", "Futsal"])
    team_files = [f for f in os.listdir('C:/Users/Diana/Desktop/Stats/Equipas') if f.endswith('.txt')]
    team_name = st.selectbox("Selecione a equipa:", team_files)
    tempo_parte = st.number_input("Duração da parte (minutos):", min_value=1, value=45)
    clube_adversario = st.text_input("Nome do clube adversário")
    playing_home = st.radio("Estamos em casa ou fora?", ["Casa", "Fora"]) == "Casa"

    if st.button("Confirmar Configuração"):
        st.session_state.modalidade = modalidade
        st.session_state.tempo_parte = tempo_parte
        st.session_state.clube_adversario = clube_adversario
        st.session_state.playing_home = playing_home
        st.session_state.team_name = team_name
        load_players(team_name)
        st.session_state.page = 2

# ======================
# Página 2 - Seleção dos Titulares
# ======================
if st.session_state.page == 2:
    st.title("⚽ Seleção dos Titulares")
    num_titulares = st.number_input("Número de titulares:", min_value=1, max_value=11, value=5)
    jogadores_selecionados = []

    if len(st.session_state.players) >= num_titulares:
        for i in range(num_titulares):
            jogador = st.selectbox(
                f"Titular {i+1}:",
                [j for j in st.session_state.players['Jogador'] if j not in jogadores_selecionados],
                key=f'sel_{i}'
            )
            jogadores_selecionados.append(jogador)

        if st.button("Confirmar Titulares"):
            for jogador in jogadores_selecionados:
                idx = st.session_state.players[st.session_state.players['Jogador']==jogador].index[0]
                st.session_state.players.at[idx, 'Em jogo'] = True
            st.session_state.page = 3  # Página do jogo
    else:
        st.warning("O número de jogadores no ficheiro é menor que o número de titulares definido.")

# ======================

# ======================
# Página 3 - Jogo
# ======================
if st.session_state.page == 3:
    st.title(f"{team_names_map.get(st.session_state.team_name, st.session_state.team_name)} vs {st.session_state.clube_adversario}")

    # Cronómetro
    update_time()
    if st.session_state.modalidade == "Futebol":
        minutos = int(st.session_state.elapsed_time // 60)
        segundos = int(st.session_state.elapsed_time % 60)
    else:
        tempo_restante = st.session_state.tempo_parte*60 - st.session_state.elapsed_time
        minutos = int(tempo_restante // 60)
        segundos = int(tempo_restante % 60)

    parte_texto = "1ª Parte" if st.session_state.part == 1 else "2ª Parte"
    st.markdown(f"### ⏱️ {parte_texto} - Tempo: {minutos:02d}:{segundos:02d}")

    # Placar e faltas
    if st.session_state.playing_home:
        placar_text = f"{team_names_map.get(st.session_state.team_name)} {st.session_state.score['Nossa']} - {st.session_state.score['Adversário']} {st.session_state.clube_adversario}"
        faltas_text = f"Faltas: {st.session_state.faltas_nossa} / {st.session_state.faltas_adversario}"
    else:
        placar_text = f"{st.session_state.clube_adversario} {st.session_state.score['Adversário']} - {team_names_map.get(st.session_state.team_name)} {st.session_state.score['Nossa']}"
        faltas_text = f"Faltas: {st.session_state.faltas_adversario} / {st.session_state.faltas_nossa}"

    st.markdown(f"### {placar_text}")
    st.markdown(f"#### {faltas_text}")

    # ======================
    # Botão Golo do Adversário
    # ======================
    col_adv1, col_adv2 = st.columns([1,1])
    with col_adv1:
        if st.button("-1 Golo adv", key="golo_adversario_minus"):
            st.session_state.score['Adversário'] -= 1
            if st.session_state.score['Adversário'] < 0:
                st.session_state.score['Adversário'] = 0
    with col_adv2:
        if st.button("+1 Golo adv", key="golo_adversario_plus"):
            st.session_state.score['Adversário'] += 1


    # Botões de controle
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("▶️ Iniciar / Retomar"):
            st.session_state.game_started = True
            if st.session_state.start_time is None:
                st.session_state.start_time = time.time() - st.session_state.elapsed_time
    with col2:
        if st.button("⏸️ Pausar"):
            st.session_state.game_started = False
    with col3:
        if st.button("⏹️ Resetar"):
            st.session_state.game_started = False
            st.session_state.start_time = None
            st.session_state.elapsed_time = 0
            st.session_state.score = {"Nossa":0, "Adversário":0}
            st.session_state.faltas_nossa = 0
            st.session_state.faltas_adversario = 0
            st.session_state.players['Tempo de Jogo'] = 0
    with col4:
        if st.button("🔄 Atualizar"):
            pass  # força atualização da página

    # Início 2ª parte / Final do jogo
    if st.session_state.elapsed_time >= st.session_state.tempo_parte*60 and st.session_state.part == 1:
        st.warning("⏸️ Intervalo - 1ª Parte terminada")
        if st.button("Início 2ª Parte"):
            st.session_state.part = 2
            st.session_state.start_time = None
            st.session_state.elapsed_time = 0
            st.session_state.faltas_nossa = 0
            st.session_state.faltas_adversario = 0

    if st.session_state.part == 2 and st.session_state.elapsed_time >= st.session_state.tempo_parte*60:
        if st.button("Final do jogo"):
            st.session_state.game_started = False
            st.success("⚽ Jogo terminado!")

    # ======================
    # Barra lateral de eventos
    # ======================
    st.sidebar.subheader("Selecionar jogador")
    em_jogo = st.session_state.players[st.session_state.players['Em jogo']==True]
    if not em_jogo.empty:
        selected_player = st.sidebar.selectbox("Jogador:", em_jogo['Jogador'])
        idx = st.session_state.players[st.session_state.players['Jogador']==selected_player].index[0]

        st.sidebar.subheader("Eventos")
        eventos = ['Golos','Assistências','Perdas de Bola','Recuperações','Amarelos','Vermelhos','Remates à Baliza','Remates Fora','Faltas Cometidas','Faltas Sofridas','Defesas']
        for ev in eventos:
            col_ev = st.sidebar.columns([2,1,1])
            col_ev[0].markdown(ev)
            if st.session_state.game_started:
                if col_ev[1].button("-1", key=f"minus_{ev}"):
                    add_stat(idx, ev, -1)
                if col_ev[2].button("+1", key=f"plus_{ev}"):
                    add_stat(idx, ev, 1)
            else:
                col_ev[1].button("-1", key=f"minus_{ev}_disabled", disabled=True)
                col_ev[2].button("+1", key=f"plus_{ev}_disabled", disabled=True)

    # ======================
    # Substituições
    # ======================
    st.subheader("🔄 Substituições")
    banco = st.session_state.players[st.session_state.players['Em jogo']==False]
    if not em_jogo.empty and not banco.empty:
        out_player = st.selectbox("Jogador a sair (Em jogo):", em_jogo['Jogador'], key='out_player')
        in_player = st.selectbox("Jogador a entrar (Banco):", banco['Jogador'], key='in_player')
        if st.button("Confirmar Substituição"):
            idx_out = st.session_state.players[st.session_state.players['Jogador']==out_player].index[0]
            idx_in = st.session_state.players[st.session_state.players['Jogador']==in_player].index[0]
            substitute_player(idx_out, idx_in)

    # ======================
    # Tabela de jogadores
    # ======================
    def style_player(row):
        cor = ''
        if row['Vermelhos'] > 0:
            cor = 'background-color: red'
        elif row['Amarelos'] > 0:
            cor = 'background-color: yellow'
        return [cor]*len(row)

    st.dataframe(st.session_state.players.style.apply(style_player, axis=1), use_container_width=True)




