import flet as ft
import pymysql
import json
import datetime
import asyncio
import winotify as win

def main(page:ft.Page):
    page.title = 'Sistema de Alerta 2v'
    page.window.maximized = True
    page.theme = ft.Theme(color_scheme_seed=ft.colors.BLUE)
    page.fonts = {
        "Poppins": "fonts/Poppins-Bold.ttf",
        "Poppins2": "fonts/Poppins-Light.ttf",
        "Poppins3": "fonts/Poppins-Regular.ttf",
    }
    loading_animation = ft.ProgressRing(width=50, height=50, visible=False)

    async def Snackbar(message: str, color: str):
        page.snack_bar = ft.SnackBar(ft.Text(message, color="White", style="Poppins"))
        page.snack_bar.open = True
        page.snack_bar.bgcolor = color
        page.update()
        await asyncio.sleep(2)
        page.snack_bar.open = False
        page.update()


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
    def deletar(id_user):
        conn = conectar()
        if conn:
            try:
                cur = conn.cursor()
                query = "DELETE FROM formulario WHERE id=%s"
                cur.execute(query, id_user)
                conn.commit()
            except pymysql.MySQLError as err:
                Snackbar(f"Erro ao inserir dados: {err}", 'Red')
            finally:
                conn.close()

        atualizar_lista()
    async def salvar_atualizacoes(e, id_user, nome_field, nf_field, data_field, status_field, editar_observacao, alerta_dialogo):
        # Pegue os valores dos campos de entrada
        nome_atualizado = nome_field.value
        nf_atualizado = nf_field.value
        data_atualizada = data_field.value
        status_atualizado = status_field.value
        observacao_atualizado = editar_observacao.value 

        # Validações (opcional)
        if not nome_atualizado or not nf_atualizado or not data_atualizada or not status_atualizado:
            await Snackbar("Preencha todos os campos antes de salvar.", "Red")
            return
        if not observacao_atualizado:
            conn = conectar()
            cur = conn.cursor()
            query = "INSERT INTO formulario (nome, NF, data, status, obs) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(query, (nome_atualizado, int(nf_atualizado), data_atualizada, status_atualizado, observacao_atualizado))
            conn.commit()
            await Snackbar('Dados inseridos com sucesso!', 'Green')
            atualizar_lista()
        else:
            conn = conectar()
            try:
                cur = conn.cursor()
                query = """
                    UPDATE formulario 
                    SET nome = %s, NF = %s, data = %s, status = %s, obs = %s 
                    WHERE id = %s
                """
                cur.execute(query, (nome_atualizado, nf_atualizado, data_atualizada, status_atualizado, observacao_atualizado, id_user))
                conn.commit()
                await Snackbar("Atualizações salvas com sucesso!", "Green")
                atualizar_lista()
                alerta_dialogo.open = False
            except pymysql.MySQLError as err:
                await Snackbar(f"Erro ao salvar alterações: {err}", "Red")
            finally:
                conn.close()

    async def inserir_info(e):
        nonlocal selected_date
        nome = fornecedor.value
        nf_env = nf.value
        obs = observação.value
        obs_vazio = ''
        
        if not nome or not nf_env or not selected_date or not status.value:
            await Snackbar('Preencha todos os campos antes de inserir.', 'Red')
            return
        # aqui eu coloquei para que se o usuario nao inserir nada no campo de obs, ele mande msm assim para o banco com o value '', para que nao de erro nos novos registros do banco
        if not obs:
            conn = conectar()
            cur = conn.cursor()
            query = "INSERT INTO formulario (nome, NF, data, status,obs) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(query, (nome, int(nf_env), selected_date, status.value, obs_vazio))
            conn.commit()
            await Snackbar('Dados inseridos com sucesso!', 'Green')
            atualizar_lista()
        else:
            conn = conectar()
            if conn:
                try:
                    cur = conn.cursor()
                    query = "INSERT INTO formulario (nome, NF, data, status,obs) VALUES (%s, %s, %s, %s, %s)"
                    cur.execute(query, (nome, int(nf_env), selected_date, status.value, obs))
                    conn.commit()
                    await Snackbar('Dados inseridos com sucesso!', 'Green')
                    atualizar_lista()
                except pymysql.MySQLError as err:
                    await Snackbar(f"Erro ao inserir dados: {err}", 'Red')
                finally:
                    conn.close()
            atualizar_lista()

    async def data_escolhida(e):
        nonlocal selected_date
        selected_date = e.control.value
        await Snackbar(f'Data selecionada: {selected_date}', 'Orange')

    list_topo = ['ID', 'FORNECEDOR', 'NF', 'DATA REGISTRADA', 'STATUS']
    columns = [ft.DataColumn(ft.Text(col, font_family='Poppins', size=14)) for col in list_topo]
    tabela = ft.DataTable(columns=columns, rows=[])

    def abrir_editar(e):
        conn = conectar()
        cur = conn.cursor()
        try:
            # Supondo que o ID esteja na primeira célula da linha selecionada
            id_user = int(e.control.cells[0].content.value)

            # Consulta para buscar os dados do registro
            cur.execute("""SELECT nome, NF, data, status, obs FROM formulario WHERE id = %s""", [id_user])
            nome, nf, data, status, observacao = cur.fetchone()

            # Campos de edição
            editar_nome = ft.TextField(
                label='Nome do Fornecedor',
                value=nome,
                show_cursor=True,
                focused_border_color=ft.colors.PURPLE,
                text_style=ft.TextStyle(font_family='Poppins3')
            )
            editar_nf = ft.TextField(
                label='NF:',
                value=nf,
                show_cursor=True,
                focused_border_color=ft.colors.PURPLE,
                text_style=ft.TextStyle(font_family='Poppins3')
            )
            editar_data = ft.TextField(
                label='Data:',
                value=data,
                show_cursor=True,
                focused_border_color=ft.colors.PURPLE,
                text_style=ft.TextStyle(font_family='Poppins3')
            )
            editar_status = ft.TextField(
                label='Status',
                value=status,
                show_cursor=True,
                focused_border_color=ft.colors.PURPLE,
                text_style=ft.TextStyle(font_family='Poppins3')
            )
            editar_observacao = ft.TextField(
                label='Observação',
                value=observacao or "",  # Use valor vazio se `observacao` for None
                show_cursor=True,
                focused_border_color=ft.colors.PURPLE,
                text_style=ft.TextStyle(font_family='Poppins3'),
                multiline=True,
                min_lines=5
            )

            # Alerta de edição
            alerta_dialogo = ft.AlertDialog(
                title=ft.Text(f"📝 Editar Funcionário {nome}", font_family='Poppins'),
                content=ft.Column([
                    editar_nome,
                    editar_nf,
                    editar_data,
                    editar_status,
                    editar_observacao
                ]),
                actions=[
                    ft.ElevatedButton(
                        'Deletar',
                        bgcolor='Red',
                        color='White',
                        icon=ft.icons.DELETE_FOREVER,
                        on_click=lambda e: deletar(id_user)
                    ),
                    ft.ElevatedButton(
                        'Salvar',
                        bgcolor='Green',
                        color='White',
                        icon=ft.icons.REFRESH,
                        on_click=lambda e: salvar_atualizacoes(
                            e, id_user, editar_nome, editar_nf, editar_data, editar_status, editar_observacao, alerta_dialogo
                        )
                    )
                ],
                actions_alignment='spaceBetween'
            )
            # Adiciona o diálogo à página e atualiza
            page.overlay.append(alerta_dialogo)
            alerta_dialogo.open = True
            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Erro ao abrir edição: {ex}"),
                bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()

        finally:
            conn.close()
            atualizar_lista()


    def ver_confirmados():
        ...
    def atualizar_lista(filtro=""):
        conn = conectar()
        if conn:
            try:
                cur = conn.cursor()
                query = """
                    SELECT id,nome,nf,data,status 
                    FROM formulario
                    WHERE status IN ('PENDENTE', 'EM ANDAMENTO') 
                    AND (nome LIKE %s OR NF LIKE %s)
                """
                cur.execute(query, (f"%{filtro}%", f"%{filtro}%"))
                informacao = cur.fetchall()
                rows = [
                    ft.DataRow(
                        cells=[ft.DataCell(ft.Text(str(item))) for item in linha],
                        on_select_changed=lambda e: abrir_editar(e),
                    )
                    for linha in informacao
                ]
                tabela.rows = rows
                page.update()
            except pymysql.MySQLError as e:
                Snackbar(f'Erro ao listar dados: {e}', 'Red')
            finally:
                conn.close()

    titulo_app = ft.Text('SDA - Fornecedor',font_family='Poppins',size=24,color='White')
    fornecedor = ft.TextField(label='Fornecedor:', focused_border_color=ft.colors.PURPLE, show_cursor=True,text_style=ft.TextStyle(font_family='Poppins3'))
    nf = ft.TextField(label='NF:', show_cursor=True,focused_border_color=ft.colors.PURPLE,text_style=ft.TextStyle(font_family='Poppins3'))
    observação = ft.TextField(label='Observação',show_cursor=True,focused_border_color=ft.colors.PURPLE,text_style=ft.TextStyle(font_family='Poppins3'),multiline=True,min_lines=5)
    progress_ring = ft.ProgressRing(visible=False)

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
    atualizar_lista()

    refresh = ft.ElevatedButton(text='Atualizar',icon=ft.icons.REFRESH, on_click=lambda e: atualizar_lista())
    inserir = ft.ElevatedButton('Inserir', bgcolor='Green', color='white', on_click=inserir_info,width=250)
    search = ft.TextField(label='Filtrar..',
            text_style=ft.TextStyle(font_family='Poppins3'),
            border_color=ft.colors.PURPLE,
            focused_border_color='Green',
            on_change=lambda e: atualizar_lista(e.control.value))

  
    scrollable_table = ft.Column(
        controls=[tabela],
        scroll=ft.ScrollMode.AUTO,
        height=740,
    )

    
    forms = ft.Container(
        content=ft.Column(
            [   
                titulo_app,
                fornecedor,
                nf,
                data_picker_button,
                status,
                observação,
                inserir
            ],
            spacing=20
        ),
        padding=40,
        margin=5,
        width=page.window.width * 0.4,
        border_radius=30,
        border=ft.border.all(2, ft.colors.PURPLE)
    )

    layout = ft.Container(
        content=ft.Column(
            [
                
                search,
                scrollable_table,
                refresh,
                progress_ring
            ],
        ),
        padding=40,
        margin=5,
        width=page.window.width * 0.9,
        border_radius=30,
        border=ft.border.all(2, ft.colors.PURPLE)
    )

    row_layout = ft.Row(
        controls=[forms, layout],
        expand=True
    )

    page.add(row_layout)

ft.app(target=main)
