from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage

import qrcode
from PIL import Image as PILImage
import io
import os


# --- Paleta de cores ---
COR_FUNDO       = (0.08, 0.08, 0.10, 1)
COR_CARD        = (0.13, 0.13, 0.16, 1)
COR_ACENTO      = (0.29, 0.56, 1.00, 1)
COR_ACENTO_ESC  = (0.18, 0.38, 0.78, 1)
COR_TEXTO       = (0.95, 0.95, 0.97, 1)
COR_TEXTO_MUTED = (0.55, 0.55, 0.62, 1)
COR_BORDA       = (0.22, 0.22, 0.28, 1)
COR_SUCESSO     = (0.20, 0.78, 0.56, 1)
COR_ERRO        = (0.95, 0.35, 0.35, 1)

Window.clearcolor = COR_FUNDO
Window.size = (480, 750)


def rgba_para_hex(r, g, b, a=1):
    return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))


class CartaoFundo(BoxLayout):
    """BoxLayout com fundo arredondado estilo card."""
    def __init__(self, cor=None, raio=12, **kwargs):
        super().__init__(**kwargs)
        self._cor = cor or COR_CARD
        self._raio = raio
        self.bind(pos=self._redesenhar, size=self._redesenhar)

    def _redesenhar(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._cor)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._raio])


class BotaoPrincipal(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = COR_TEXTO
        self.font_size = dp(15)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(50)
        self.bind(pos=self._redesenhar, size=self._redesenhar)

    def _redesenhar(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COR_ACENTO)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

    def on_press(self):
        with self.canvas.before:
            Color(*COR_ACENTO_ESC)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

    def on_release(self):
        self._redesenhar()


class BotaoSecundario(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = COR_ACENTO
        self.font_size = dp(14)
        self.size_hint_y = None
        self.height = dp(44)
        self.bind(pos=self._redesenhar, size=self._redesenhar)

    def _redesenhar(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COR_BORDA)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])


class CampoTexto(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0.10, 0.10, 0.13, 1)
        self.foreground_color = COR_TEXTO
        self.cursor_color = COR_ACENTO
        self.hint_text_color = (*COR_TEXTO_MUTED[:3], 0.6)
        self.padding = [dp(14), dp(12)]
        self.font_size = dp(14)
        self.size_hint_y = None
        self.height = dp(48)
        self.multiline = False


class Rotulo(Label):
    def __init__(self, muted=False, tamanho=14, **kwargs):
        super().__init__(**kwargs)
        self.color = COR_TEXTO_MUTED if muted else COR_TEXTO
        self.font_size = dp(tamanho)
        self.size_hint_y = None
        self.height = dp(tamanho + 10)
        self.halign = "left"
        self.valign = "middle"
        self.bind(size=lambda *a: setattr(self, "text_size", self.size))


class GeradorQRLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(16), **kwargs)

        self._qr_pil = None
        self._cor_frente = (0, 0, 0)
        self._cor_fundo  = (1, 1, 1)

        self._construir_ui()

    # ------------------------------------------------------------------ UI ---

    def _construir_ui(self):
        # Título
        titulo = Label(
            text="QR Code Generator",
            font_size=dp(26),
            bold=True,
            color=COR_TEXTO,
            size_hint_y=None,
            height=dp(50),
            halign="left",
            valign="middle",
        )
        titulo.bind(size=lambda *a: setattr(titulo, "text_size", titulo.size))
        self.add_widget(titulo)

        subtitulo = Rotulo(
            text="Cole um link e personalize seu QR code",
            muted=True,
            tamanho=13,
        )
        self.add_widget(subtitulo)

        # --- Card de entrada ---
        card_entrada = CartaoFundo(orientation="vertical", padding=dp(16), spacing=dp(12),
                                   size_hint_y=None, height=dp(180))

        card_entrada.add_widget(Rotulo(text="Link ou texto", tamanho=12, muted=True))

        self.campo_link = CampoTexto(hint_text="https://exemplo.com")
        card_entrada.add_widget(self.campo_link)

        # Linha: tamanho
        linha_tam = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        linha_tam.add_widget(Rotulo(text="Tamanho:", tamanho=13, size_hint_x=0.35))
        self.slider_tamanho = Slider(min=150, max=400, value=250, step=10, size_hint_x=0.5)
        self.slider_tamanho.bind(value=self._atualizar_label_tamanho)
        self.label_tamanho = Rotulo(text="250px", tamanho=13, muted=True, size_hint_x=0.15)
        linha_tam.add_widget(self.slider_tamanho)
        linha_tam.add_widget(self.label_tamanho)
        card_entrada.add_widget(linha_tam)

        # Linha: correção de erros
        linha_ec = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        linha_ec.add_widget(Rotulo(text="Correção de erro:", tamanho=13, size_hint_x=0.5))
        self.btn_ec = BotaoSecundario(text="Alta (H)", size_hint_x=0.5)
        self._ec_opcoes = ["Baixa (L)", "Média (M)", "Alta (Q)", "Máxima (H)"]
        self._ec_valores = ["L", "M", "Q", "H"]
        self._ec_idx = 3
        self.btn_ec.bind(on_press=self._ciclar_ec)
        linha_ec.add_widget(self.btn_ec)
        card_entrada.add_widget(linha_ec)

        self.add_widget(card_entrada)

        # --- Card de cores ---
        card_cores = CartaoFundo(orientation="horizontal", padding=dp(16), spacing=dp(12),
                                  size_hint_y=None, height=dp(70))

        card_cores.add_widget(Rotulo(text="Cores:", tamanho=13, size_hint_x=0.25))

        btn_cor_frente = BotaoSecundario(text="Código", size_hint_x=0.375)
        btn_cor_frente.bind(on_press=lambda *a: self._abrir_color_picker("frente"))
        self.btn_cor_frente = btn_cor_frente

        btn_cor_fundo = BotaoSecundario(text="Fundo", size_hint_x=0.375)
        btn_cor_fundo.bind(on_press=lambda *a: self._abrir_color_picker("fundo"))
        self.btn_cor_fundo = btn_cor_fundo

        card_cores.add_widget(btn_cor_frente)
        card_cores.add_widget(btn_cor_fundo)
        self.add_widget(card_cores)

        # --- Botão gerar ---
        btn_gerar = BotaoPrincipal(text="Gerar QR Code")
        btn_gerar.bind(on_press=self._gerar)
        self.add_widget(btn_gerar)

        # --- Área de preview ---
        self.card_preview = CartaoFundo(
            orientation="vertical", padding=dp(20), spacing=dp(10),
            size_hint_y=None, height=dp(320),
        )

        self.img_qr = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.card_preview.add_widget(self.img_qr)

        self.label_status = Label(
            text="Preencha o link e clique em Gerar",
            color=(*COR_TEXTO_MUTED[:3], 0.7),
            font_size=dp(13),
            size_hint_y=None,
            height=dp(30),
        )
        self.card_preview.add_widget(self.label_status)

        self.add_widget(self.card_preview)

        # --- Botões de salvar ---
        linha_salvar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))

        btn_salvar = BotaoSecundario(text="Salvar PNG")
        btn_salvar.bind(on_press=self._salvar_png)
        linha_salvar.add_widget(btn_salvar)

        btn_salvar_svg = BotaoSecundario(text="Salvar SVG")
        btn_salvar_svg.bind(on_press=self._salvar_svg)
        linha_salvar.add_widget(btn_salvar_svg)

        self.add_widget(linha_salvar)

    # ---------------------------------------------------------- Callbacks ---

    def _atualizar_label_tamanho(self, slider, valor):
        self.label_tamanho.text = f"{int(valor)}px"

    def _ciclar_ec(self, *args):
        self._ec_idx = (self._ec_idx + 1) % 4
        self.btn_ec.text = self._ec_opcoes[self._ec_idx]

    def _abrir_color_picker(self, alvo):
        conteudo = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        picker = ColorPicker()
        conteudo.add_widget(picker)

        btn_ok = BotaoPrincipal(text="Confirmar")
        conteudo.add_widget(btn_ok)

        popup = Popup(
            title="Escolher cor",
            content=conteudo,
            size_hint=(0.9, 0.85),
            background_color=(*COR_CARD[:3], 1),
            title_color=COR_TEXTO,
        )

        def confirmar(*a):
            r, g, b, _ = picker.color
            if alvo == "frente":
                self._cor_frente = (r, g, b)
                self.btn_cor_frente.text = f"Código ●"
            else:
                self._cor_fundo = (r, g, b)
                self.btn_cor_fundo.text = f"Fundo ●"
            popup.dismiss()

        btn_ok.bind(on_press=confirmar)
        popup.open()

    def _gerar(self, *args):
        link = self.campo_link.text.strip()
        if not link:
            self._mostrar_status("Insira um link ou texto!", erro=True)
            return

        try:
            ec_map = {"L": qrcode.constants.ERROR_CORRECT_L,
                      "M": qrcode.constants.ERROR_CORRECT_M,
                      "Q": qrcode.constants.ERROR_CORRECT_Q,
                      "H": qrcode.constants.ERROR_CORRECT_H}

            nivel = ec_map[self._ec_valores[self._ec_idx]]
            tamanho = int(self.slider_tamanho.value)

            qr = qrcode.QRCode(
                version=1,
                error_correction=nivel,
                box_size=10,
                border=4,
            )
            qr.add_data(link)
            qr.make(fit=True)

            cor_frente = rgba_para_hex(*self._cor_frente)
            cor_fundo  = rgba_para_hex(*self._cor_fundo)

            pil_img = qr.make_image(fill_color=cor_frente, back_color=cor_fundo)
            pil_img = pil_img.resize((tamanho, tamanho), PILImage.NEAREST)
            self._qr_pil = pil_img

            # Converter PIL → textura Kivy
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            buf.seek(0)
            core_img = CoreImage(buf, ext="png")
            self.img_qr.texture = core_img.texture

            self._mostrar_status("QR code gerado com sucesso!", erro=False)

        except Exception as e:
            self._mostrar_status(f"Erro: {e}", erro=True)

    def _mostrar_status(self, msg, erro=False):
        self.label_status.color = (*COR_ERRO[:3], 0.9) if erro else (*COR_SUCESSO[:3], 0.9)
        self.label_status.text = msg
        Clock.schedule_once(lambda *a: setattr(
            self.label_status, "color", (*COR_TEXTO_MUTED[:3], 0.7)
        ), 4)

    def _salvar_png(self, *args):
        if self._qr_pil is None:
            self._mostrar_status("Gere um QR code primeiro!", erro=True)
            return
        caminho = os.path.join(os.path.expanduser("~"), "qrcode.png")
        self._qr_pil.save(caminho)
        self._mostrar_status(f"Salvo em: {caminho}")

    def _salvar_svg(self, *args):
        if self._qr_pil is None:
            self._mostrar_status("Gere um QR code primeiro!", erro=True)
            return
        try:
            import qrcode.image.svg as qr_svg
            import xml.etree.ElementTree as ET

            link = self.campo_link.text.strip()
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
            qr.add_data(link)
            qr.make(fit=True)
            factory = qr_svg.SvgPathImage
            img_svg = qr.make_image(image_factory=factory)

            caminho = os.path.join(os.path.expanduser("~"), "qrcode.svg")
            img_svg.save(caminho)
            self._mostrar_status(f"SVG salvo em: {caminho}")
        except Exception as e:
            self._mostrar_status(f"Erro ao salvar SVG: {e}", erro=True)


class GeradorQRApp(App):
    def build(self):
        self.title = "QR Code Generator"

        scroll = ScrollView()
        layout = GeradorQRLayout(size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))
        scroll.add_widget(layout)
        return scroll


if __name__ == "__main__":
    GeradorQRApp().run()