import flet as ft
import pymysql
import json
import time
import datetime

def main(page:ft.Page):
    page.title = 'Sistema de Alerta 2v'
    page.window_maximizable = True
    page.theme = ft.Theme(color_scheme_seed=ft.colors.BLUE)
    page.fonts = {
        "Poppins": "fonts/Poppins-Bold.ttf",
        "Poppins2": "fonts/Poppins-Light.ttf",
        "Poppins3": "fonts/Poppins-Regular.ttf",
    }
    
    def Snackbar(message:str, color:str):
        page.snack_bar = ft.SnackBar(ft.Text(message, color="White", style="Poppins"))
        page.snack_bar.open = True
        page.snack_bar.bgcolor = color
        page.update()
        time.sleep(2)

    def conectar():
        with open('config.json', 'r') as f:
            config = json.load(f)
        try:
            connection = pymysql.connect(
                host=config['host'],
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
            return connection
        except pymysql.MySQLError as e:
            Snackbar(f'Erro no banco {e}', 'Red')
            return None

    selected_date = None  # Variável para armazenar a data selecionada
    # Deletar formulario
    def deletar(i):
        conn = conectar()
        if conn:
            try:
                cur = conn.cursor()
                query = "DELETE FROM formulario WHERE id=%s"
                cur.execute(query, i)
                conn.commit()
            except pymysql.MySQLError as err:
                Snackbar(f"Erro ao inserir dados: {err}", 'Red')
            finally:
                conn.close()

    def inserir_info(e):
        nonlocal selected_date
        nome = fornecedor.value
        nf_env = nf.value
        if not nome or not nf_env or not selected_date or not status.value:
            Snackbar('Preencha todos os campos antes de inserir.', 'Red')
            return
        conn = conectar()
        if conn:
            try:
                cur = conn.cursor()
                query = "INSERT INTO formulario (nome, NF, data, status) VALUES (%s, %s, %s, %s)"
                cur.execute(query, (nome, nf_env, selected_date, status.value))
                conn.commit()
                Snackbar('Dados inseridos com sucesso!', 'Green')
                atualizar_lista()  # Atualizar tabela após inserção
            except pymysql.MySQLError as err:
                Snackbar(f"Erro ao inserir dados: {err}", 'Red')
            finally:
                conn.close()

    def data_escolhida(e):
        nonlocal selected_date
        selected_date = e.control.value
        Snackbar(f'Data selecionada: {selected_date}', 'Orange')

    list_topo = ['ID', 'FORNECEDOR', 'NF', 'DATA REGISTRADA', 'STATUS']
    columns = [ft.DataColumn(ft.Text(col, font_family='Poppins', size=14)) for col in list_topo]
    tabela = ft.DataTable(columns=columns, rows=[])  
    def atualizar_lista():
        conn = conectar()
        if conn:
            try:
                cur = conn.cursor()
                query = "SELECT * FROM formulario ORDER BY status DESC"
                cur.execute(query)
                informacao = cur.fetchall()
                rows = [
                    ft.DataRow(cells=[ft.DataCell(ft.Text(str(item))) for item in linha],on_select_changed=deletar)
                    for linha in informacao
                ]
                tabela.rows = rows
                page.update()
            except pymysql.MySQLError as e:
                Snackbar(f'Erro ao listar dados: {e}', 'Red')
            finally:
                conn.close()

    fornecedor = ft.TextField(label='Fornecedor:', enable_suggestions=True, show_cursor=True)
    nf = ft.TextField(label='NF:', show_cursor=True)
    
    data_picker_button = ft.ElevatedButton(
        "Selecione a Data",
        icon=ft.icons.CALENDAR_MONTH,
        on_click=lambda e: page.open(
            ft.DatePicker(
                first_date=datetime.datetime(year=2020, month=1, day=1),
                last_date=datetime.datetime(year=2030, month=1, day=1),
                on_change=data_escolhida
            )
        ),
    )

    status = ft.Dropdown(
        label='Status',
        options=[
            ft.dropdown.Option('PENDENTE'),
            ft.dropdown.Option('EM ANDAMENTO'),
            ft.dropdown.Option('CONFIRMADO')
        ]
    )
    
    botao = ft.ElevatedButton('Inserir', bgcolor='Green', color='white', on_click=inserir_info)


    atualizar_lista()

    refresh = ft.ElevatedButton('Atualizar', icon=ft.icons.REFRESH, on_click=lambda e: atualizar_lista())

    

    # Envolva a `DataTable` em uma `Column` com `scroll` e defina a altura
    scrollable_table = ft.Column(
        controls=[tabela],
        scroll=ft.ScrollMode.AUTO,  # Aplicando scroll à Column
        height=850,  # Definindo altura da área de rolagem
    )

    
    forms = ft.Container(
        content=ft.Column(
            [
                fornecedor,
                nf,
                data_picker_button,
                status,
                refresh,
                botao
            ],
            spacing=20
        ),
        padding=40,
        margin=5,
        width=page.window_width * 0.3,
        border_radius=30,
        border=ft.border.all(2, ft.colors.BLACK)
    )

    layout = ft.Container(
        content=ft.Column(
            [
                scrollable_table
            ],
            spacing=20
        ),
        padding=40,
        margin=5,
        width=page.window_width * 0.7,
        border_radius=30,
        border=ft.border.all(2, ft.colors.BLACK)
    )

    row_layout = ft.Row(
        controls=[forms, layout],
        expand=True
    )

    page.add(row_layout)

ft.app(target=main)
