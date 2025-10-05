import streamlit as st
import pandas as pd
import time
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Estatísticas Ao Vivo", layout="wide")

# ======================
# CSS para desativar pull-to-refresh em dispositivos móveis
# ======================
st.markdown("""
    <style>
    html, body {
        overscroll-behavior-y: contain;
        touch-action: pan-x pan-y;
    }
    </style>
""", unsafe_allow_html=True)

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
    st.session_state.score = {"Nossa": 0, "Adversário": 0}
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
if 'event_log' not in st.session_state:
    st.session_state.event_log = []

# Caminho das equipas
equipas_path = "Equipas"
team_files = [f for f in os.listdir(equipas_path) if f.endswith('.txt')]

# Mapear ficheiros para nomes
team_names_map = {
    "condeixa.txt": "Condeixa",
    "santaclara.txt": "Santa Clara"
}

# ======================
# Carregar jogadores
# ======================
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
                    'Golos': 0,
                    'Assistências': 0,
                    'Perdas de Bola': 0,
                    'Recuperações': 0,
                    'Amarelos': 0,
                    'Vermelhos': 0,
                    'Remates à Baliza': 0,
                    'Remates Fora': 0,
                    'Faltas Cometidas': 0,
                    'Faltas Sofridas': 0,
                    'Defesas': 0,
                    'Tempo de Jogo': 0
                })
    st.session_state.players = pd.DataFrame(players_list)

# ======================
# Funções auxiliares
# ======================
def create_or_update_file(repo, path, commit_message, content):
    """
    Cria um arquivo no GitHub se não existir ou atualiza se já existir.
    """
    try:
        repo.create_file(path, commit_message, content)
    except:
        contents = repo.get_contents(path)
        repo.update_file(contents.path, commit_message, content, contents.sha)

def remove_last_event(evento, jogador=None):
    if 'event_log' not in st.session_state or not st.session_state.event_log:
        return
    for i in reversed(range(len(st.session_state.event_log))):
        entry = st.session_state.event_log[i]
        if jogador:
            if evento in entry and jogador in entry:
                st.session_state.event_log.pop(i)
                break
        else:
            if evento in entry:
                st.session_state.event_log.pop(i)
                break

def log_event(descricao, value=1):
    minutos = int(st.session_state.elapsed_time // 60)
    segundos = int(st.session_state.elapsed_time % 60)
    parte = "1ª Parte" if st.session_state.part == 1 else "2ª Parte"

    # Para remover eventos (se value < 0)
    if value < 0:
        for i in reversed(range(len(st.session_state.event_log))):
            if descricao in st.session_state.event_log[i]:
                st.session_state.event_log.pop(i)
                break
        return

    # Adicionar evento
    st.session_state.event_log.append(f"{parte} {minutos:02d}:{segundos:02d} - {descricao}")

    # --- Atualizar GitHub ---
    log_text = "\n".join(st.session_state.event_log)
    players_csv = st.session_state.players.to_csv(index=False, encoding="utf-8-sig")

    create_or_update_file(repo, f"{folder_path}/{base_filename}_logbook.txt", f"Update logbook {base_filename}", log_text)
    create_or_update_file(repo, f"{folder_path}/{base_filename}_players.csv", f"Update players table {base_filename}", players_csv)


def add_stat(idx, stat, value=1):
    player_name = st.session_state.players.at[idx, 'Jogador']
    if value < 0:
        st.session_state.players.at[idx, stat] = max(0, st.session_state.players.at[idx, stat] + value)
        if stat == 'Golos':
            st.session_state.score['Nossa'] = max(0, st.session_state.score['Nossa'] + value)
            remove_last_event(f"Golo - {player_name}", player_name)
        elif stat == 'Faltas Cometidas':
            if st.session_state.playing_home:
                st.session_state.faltas_nossa = max(0, st.session_state.faltas_nossa + value)
            else:
                st.session_state.faltas_adversario = max(0, st.session_state.faltas_adversario + value)
            remove_last_event(f"Falta Cometida - {player_name}", player_name)
        elif stat == 'Faltas Sofridas':
            if st.session_state.playing_home:
                st.session_state.faltas_adversario = max(0, st.session_state.faltas_adversario + value)
            else:
                st.session_state.faltas_nossa = max(0, st.session_state.faltas_nossa + value)
            remove_last_event(f"Falta Sofrida - {player_name}", player_name)
        elif stat in ['Amarelos', 'Vermelhos']:
            st.session_state.players.at[idx, stat] = max(0, st.session_state.players.at[idx, stat])
            remove_last_event(f"{stat} - {player_name}", player_name)
        else:
            remove_last_event(f"{stat} - {player_name}", player_name)
        return
    st.session_state.players.at[idx, stat] += value
    if stat == 'Golos':
        st.session_state.score['Nossa'] += value
        log_event(f"Golo - {player_name}")
    elif stat == 'Faltas Cometidas':
        if st.session_state.playing_home:
            st.session_state.faltas_nossa += value
        else:
            st.session_state.faltas_adversario += value
        log_event(f"Falta Cometida - {player_name}")
    elif stat == 'Faltas Sofridas':
        if st.session_state.playing_home:
            st.session_state.faltas_adversario += value
        else:
            st.session_state.faltas_nossa += value
        log_event(f"Falta Sofrida - {player_name}")
    else:
        log_event(f"{stat} - {player_name}")

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

from github import Github
    
# Pegar o token do Streamlit Secrets
github_token = st.secrets["GITHUB_TOKEN"]

# Criar objeto GitHub
g = Github(github_token)

# Repositório
repo = g.get_repo("dianol3/stats")  # substitua pelo seu repo

# Nome base do arquivo
base_filename = f"{st.session_state.team_name}_VS_{st.session_state.clube_adversario}"

# Pasta onde vai guardar os arquivos
folder_path = st.session_state.team_name  # pasta com o nome da equipe selecionada

# =================
# Página 0
# ==================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page == 'home':
    st.title("⚽ Estatísticas Ao Vivo")
    
    escolha = st.radio("Escolha uma opção:", ["Novo Jogo", "Ver Jogos Guardados"], key="home_choice")
    
    if st.button("Confirmar Escolha"):
        if escolha == "Novo Jogo":
            st.session_state.page = 1
        elif escolha == "Ver Jogos Guardados":
            st.session_state.page = 'ver_jogos'
    st.stop()
    
# ================
# ver jogos
# ===============

if st.session_state.page == 'ver_jogos':
    st.title("📂 Jogos Guardados")

    # Listar pastas no repositório (cada pasta = equipa)
    from github import Github
    github_token = st.secrets["GITHUB_TOKEN"]
    g = Github(github_token)
    repo = g.get_repo("dianol3/stats")  # teu repo

    contents = repo.get_contents("")  # raiz
    pastas = [c.path for c in contents if c.type == 'dir']

    if pastas:
        pasta_selecionada = st.selectbox("Selecione a equipa:", pastas)

        # Listar arquivos dentro da pasta
        arquivos = repo.get_contents(pasta_selecionada)
        arquivos_nomes = [a.name for a in arquivos]
        arquivo_selecionado = st.selectbox("Selecione o arquivo:", arquivos_nomes)

        if st.button("Ver arquivo"):
            arquivo = repo.get_contents(f"{pasta_selecionada}/{arquivo_selecionado}")
            conteudo = arquivo.decoded_content.decode("utf-8")
            st.text_area("Conteúdo:", conteudo, height=400)

            # Botão de download
            st.download_button(
                label="📥 Download do arquivo",
                data=conteudo,
                file_name=arquivo_selecionado,
                mime="text/plain"
            )
    else:
        st.write("Nenhuma pasta encontrada no repositório.")

# Botão para voltar à página inicial
if st.button("⬅️ Voltar", key="voltar_home1"):
    st.session_state.page = 'home'
    st.stop()
st.stop()

# ======================
# Página 1 - Configuração
# ======================

if st.session_state.page == 1:
    st.title("⚽ Configuração do Jogo")
    modalidade = st.selectbox("Selecione a modalidade:", ["Futebol", "Futsal"])
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

# Botão para voltar à página inicial
if st.button("⬅️ Voltar", key="voltar_home"):
    st.session_state.page = 'home'
st.stop()
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
                idx = st.session_state.players[st.session_state.players['Jogador'] == jogador].index[0]
                st.session_state.players.at[idx, 'Em jogo'] = True
                titulares = st.session_state.players[st.session_state.players['Em jogo'] == True]
                nomes = ", ".join(titulares['Jogador'])
            log_event(f"Titulares da 1ª parte: {nomes}", value=0)
            st.session_state.page = 3
    else:
        st.warning("O número de jogadores no ficheiro é menor que o número de titulares definido.")
        
    st.stop()
# ======================
# Página 3 - Jogo
# ======================
if st.session_state.page == 3:
    if st.session_state.playing_home:
        st.title(f"{team_names_map.get(st.session_state.team_name, st.session_state.team_name)} vs {st.session_state.clube_adversario}")
    else:
        st.title(f"{st.session_state.clube_adversario} vs {team_names_map.get(st.session_state.team_name, st.session_state.team_name)}")

    update_time()

    if st.session_state.modalidade == "Futebol":
        minutos = int(st.session_state.elapsed_time // 60)
        segundos = int(st.session_state.elapsed_time % 60)
    else:
        # Futsal - contagem decrescente
        tempo_restante = st.session_state.tempo_parte*60 - st.session_state.elapsed_time
        if tempo_restante >= 0:
            minutos = int(tempo_restante // 60)
            segundos = int(tempo_restante % 60)
        else:
            # tempo negativo: -0:01, -0:02, etc
            tempo_neg = abs(tempo_restante)
            minutos = -(int(tempo_neg // 60))
            segundos = int(tempo_neg % 60)
    
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

    # ----------------------------------
    # Descontos tempo
    # ---------------------------------
    parte_atual = st.session_state.part
    
    # Inicializar estados de desconto se não existirem
    if 'desconto_nossa' not in st.session_state:
        st.session_state.desconto_nossa = {1: False, 2: False}
    if 'desconto_adversario' not in st.session_state:
        st.session_state.desconto_adversario = {1: False, 2: False}

    # Botões Golo do Adversário
    col_adv1, col_adv2 = st.columns([1, 1])
    with col_adv1:
        if st.button("-1 Golo adv", key="golo_adversario_minus"):
            st.session_state.score['Adversário'] -= 1
            if st.session_state.score['Adversário'] < 0:
                st.session_state.score['Adversário'] = 0
            remove_last_event("Golo Adversário")
    with col_adv2:
        if st.button("+1 Golo adv", key="golo_adversario_plus"):
            st.session_state.score['Adversário'] += 1
            log_event("Golo Adversário")

    # Controlo do jogo + Descontos de tempo
    col1, col2, col3, col4 = st.columns(4)
    
    # ▶️ Iniciar / Retomar
    with col1:
        if st.button("▶️ Iniciar / Retomar"):
            if not st.session_state.game_started:
                st.session_state.game_started = True
                st.session_state.start_time = time.time() - st.session_state.elapsed_time
    
    # ⏸️ Pausar
    with col2:
        if st.button("⏸️ Pausar"):
            if st.session_state.game_started:
                current_elapsed = time.time() - st.session_state.start_time
                st.session_state.elapsed_time = current_elapsed
                st.session_state.game_started = False
                st.session_state.start_time = None
    
    # Desconto tempo – Equipa da casa
    with col3:
        if st.session_state.part not in st.session_state.get('desconto_casa_part', {}):
            if st.button(f"⏱️ Desconto {team_names_map.get(st.session_state.team_name, st.session_state.team_name)}"):
                minutos = int(st.session_state.elapsed_time // 60)
                segundos = int(st.session_state.elapsed_time % 60)
                parte = "1ª Parte" if st.session_state.part == 1 else "2ª Parte"
                st.session_state.event_log.append(
                    f"{parte} {minutos:02d}:{segundos:02d} - Desconto tempo {team_names_map.get(st.session_state.team_name)}"
                )
                if 'desconto_casa_part' not in st.session_state:
                    st.session_state.desconto_casa_part = {}
                st.session_state.desconto_casa_part[st.session_state.part] = True
    
    # Botão Desconto para equipa visitante
    with col4:
        if st.session_state.part not in st.session_state.get('desconto_visit_part', {}):
            if st.button(f"⏱️ Desconto {st.session_state.clube_adversario}"):
                minutos = int(st.session_state.elapsed_time // 60)
                segundos = int(st.session_state.elapsed_time % 60)
                parte = "1ª Parte" if st.session_state.part == 1 else "2ª Parte"
                st.session_state.event_log.append(
                    f"{parte} {minutos:02d}:{segundos:02d} - Desconto tempo {st.session_state.clube_adversario}"
                )
                if 'desconto_visit_part' not in st.session_state:
                    st.session_state.desconto_visit_part = {}
                st.session_state.desconto_visit_part[st.session_state.part] = True

    st_autorefresh(interval=1000, key="refresh")

    # Início 2ª parte / Final do jogo
    if st.session_state.elapsed_time >= st.session_state.tempo_parte*60 and st.session_state.part == 1:
        st.warning("⏸️ Intervalo - 1ª Parte terminada")
        if st.button("Início 2ª Parte"):
            st.session_state.part = 2
            st.session_state.start_time = None
            st.session_state.elapsed_time = 0
            st.session_state.faltas_nossa = 0
            st.session_state.faltas_adversario = 0
            titulares = st.session_state.players[st.session_state.players['Em jogo'] == True]
            nomes = ", ".join(titulares['Jogador'])
            log_event(f"Titulares da 2ª parte: {nomes}", value=0)
                
# ======================
# Barra lateral - Eventos
# ======================
st.sidebar.subheader("Selecionar jogador")
if 'players' in st.session_state and not st.session_state.players.empty and 'Em jogo' in st.session_state.players.columns:
    em_jogo = st.session_state.players[st.session_state.players['Em jogo'] == True]
else:
    em_jogo = pd.DataFrame()

if not em_jogo.empty:
    selected_player = st.sidebar.selectbox("Jogador:", em_jogo['Jogador'])
    idx = st.session_state.players[st.session_state.players['Jogador'] == selected_player].index[0]
    st.sidebar.subheader("Eventos")
    eventos = ['Perdas de Bola','Recuperações','Remates à Baliza','Remates Fora','Defesas','Faltas Cometidas','Faltas Sofridas','Golos','Assistências','Amarelos','Vermelhos']
    for ev in eventos:
        col_ev = st.sidebar.columns([2,1,1])
        col_ev[0].markdown(ev)
        if col_ev[2].button("+1", key=f"plus_{ev}"):
            add_stat(idx, ev, 1)
        if col_ev[1].button("-1", key=f"minus_{ev}"):
            add_stat(idx, ev, -1)

# ======================
# Substituições
# ======================
st.subheader("🔄 Substituições")
if 'players' in st.session_state and not st.session_state.players.empty and 'Em jogo' in st.session_state.players.columns:
    em_jogo = st.session_state.players[st.session_state.players['Em jogo'] == True]
    banco = st.session_state.players[st.session_state.players['Em jogo'] == False]
else:
    em_jogo = pd.DataFrame()
    banco = pd.DataFrame()

if not em_jogo.empty and not banco.empty:
    out_player = st.selectbox("Jogador a sair (Em jogo):", em_jogo['Jogador'], key='out_player')
    in_player = st.selectbox("Jogador a entrar (Banco):", banco['Jogador'], key='in_player')
    if st.button("Confirmar Substituição"):
        idx_out = st.session_state.players[st.session_state.players['Jogador']==out_player].index[0]
        idx_in = st.session_state.players[st.session_state.players['Jogador']==in_player].index[0]
        substitute_player(idx_out, idx_in)
        log_event(f"Substituição - Entra {in_player}, Sai {out_player}")

# ======================
# Tabela de jogadores
# ======================
def style_player(row):
    if row['Vermelhos'] > 0:
        cor = 'background-color: red'
    elif row['Amarelos'] > 0:
        cor = 'background-color: yellow'
    else:
        cor = ''
    return [cor]*len(row)

st.dataframe(st.session_state.players.style.apply(style_player, axis=1), use_container_width=True)

# ======================
# Bloco de Notas - Log do Jogo
# ======================
st.subheader("📝 Bloco de Notas do Jogo")
if st.session_state.event_log:
    for e in st.session_state.event_log:
        st.markdown(f"- {e}")
else:
    st.write("Ainda não há eventos registados.")

