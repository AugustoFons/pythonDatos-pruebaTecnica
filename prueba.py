""" Librerias utilizadas:

    matplotlib==3.9.0
    mysql-connector-python==9.0.0
    fpdf==1.7.2
    PyPDF2==3.0.1
    pandas==2.2.2 
"""
import mysql.connector
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import PyPDF2

""" ¡¡ Configurar base de datos !! """
#config = {
#    'user': '...',
#    'password': '...',
#    'host': '...',
#   'database': 'prueba_postulantes'
#}

def connectDB():
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print("Conexión exitosa a la base de datos")
            cursor = conn.cursor()
            return conn, cursor
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None, None
    
# Consulta de datos
def fetch_data(cursor):
    query = "SELECT * FROM encuesta"
    cursor.execute(query)
    data = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
    return data

# SNG de satisfaccion
def satisfaccion_sng(data, column):
    promotores = data[data[column] >= 6].shape[0]
    detractores = data[data[column] <= 3].shape[0]
    total_respuestas = data.shape[0]
    sng = ((promotores - detractores) / total_respuestas) * 100
    return sng

# Total de personas que conocian la empresa
def total_conocia_empresa(data):
    conocia_empresa = data[data['conocia_empresa'] == 'Sí'].shape[0]
    return conocia_empresa

# SNG recomendaciones
def recomendacion_sng(data, column):
    promotores = data[data[column] >= 6].shape[0]
    detractores = data[data[column] <= 3].shape[0]
    total_respuestas = data.shape[0]
    sng = ((promotores - detractores) / total_respuestas) * 100
    return sng

# SNG promedio de recomendaciones
def promedio_recomendacion(data, column):
    return data[column].mean()

# Total de comentarios
def total_comentarios(data, columna_comentario):
    total_comentarios = data[columna_comentario].dropna().shape[0]
    return total_comentarios

# Duracion de encuesta
def calcular_duracion_encuesta(data):
    if 'fecha' in data.columns:
        fechas = pd.to_datetime(data['fecha'], format='%Y-%m-%d %H:%M:%S')
        fecha_inicio = fechas.min()
        fecha_fin = fechas.max()
        dias_transcurridos = (fecha_fin - fecha_inicio).days
        meses_transcurridos = dias_transcurridos // 30 # Considero 30 días por mes
        dias_restantes = dias_transcurridos % 30

        return dias_transcurridos, meses_transcurridos, dias_restantes
    else:
        return None, None
    
# Graficos de los calculos
def crear_graficos(data):
    plt.figure(figsize=(14, 8))

    plt.subplot(2, 2, 1)
    data['satisfeccion_general'].value_counts().sort_index().plot(kind='bar', color='skyblue')
    plt.title('Distribución de la Satisfacción General')
    plt.xlabel('Satisfacción')
    plt.ylabel('Frecuencia')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.subplot(2, 2, 2)
    data['recomendacion'].value_counts().sort_index().plot(kind='bar', color='salmon')
    plt.title('Distribución de la Recomendación')
    plt.xlabel('Recomendación')
    plt.ylabel('Frecuencia')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.subplot(2, 2, 3)
    conocia = ['Conocían', 'No Conocían']
    sizes = [total_conocia_empresa(data), len(data) - total_conocia_empresa(data)]
    plt.pie(sizes, labels=conocia, autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
    plt.title('Conocimiento de la Empresa')

    plt.subplot(2, 2, 4)
    data['recomendacion_abierta'].notnull().value_counts().plot(kind='bar', color='gold')
    plt.title('Comentarios Realizados')
    plt.xlabel('Se realizaron comentarios')
    plt.ylabel('Frecuencia')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.5)
    plt.savefig('graficos.png')
    plt.close()

# Configuración del primer archivo PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Informe de la Encuesta', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_graphics(self, image_path):
        self.image(image_path, x=10, y=self.get_y(), w=190)
        self.ln(85)

conn, cursor = connectDB()
if conn and cursor:
    data = fetch_data(cursor)
    cursor.close()
    conn.close()

    # Calcular métricas
    sng = satisfaccion_sng(data, 'satisfeccion_general')
    total_conocian = total_conocia_empresa(data)
    sng_recomendacion = recomendacion_sng(data, 'recomendacion')
    promedio_recom = promedio_recomendacion(data, 'recomendacion')
    total_comentarios_realizados = total_comentarios(data, 'recomendacion_abierta')
    dias_encuesta, meses_encuesta, diasR_encuesta = calcular_duracion_encuesta(data)

    # Crear gráficos
    crear_graficos(data)

    # Crear PDF con los calculos y gráficos
    pdf = PDF()
    pdf.add_page()

    pdf.chapter_title('Resultados obtenidos:')
    pdf.chapter_body(
        f"SNG de satisfacción general: {sng:.2f}%\n"
        f"Total de personas que conocían a la empresa: {total_conocian}\n"
        f"SNG de recomendación: {sng_recomendacion:.2f}%\n"
        f"Nota promedio de la recomendación: {promedio_recom:.2f}\n"
        f"Total de personas que hicieron un comentario: {total_comentarios_realizados}\n"
        f"Días que lleva la encuesta: {dias_encuesta} días\n"
        f"La encuesta lleva {meses_encuesta} meses y {diasR_encuesta} días\n"
    )

    pdf.chapter_title('Gráficos: ')
    pdf.add_graphics('graficos.png')

    pdf.output('Informe_encuesta.pdf')

    print("Informe de métricas PDF creado exitosamente.")

else:
    print("No se pudo establecer la conexión a la base de datos.")


### Analisis de sentimiento de ChatGPT ###

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.title_added = False

    def header(self):
        if self.page_no() == 1 and not self.title_added:
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "Informe sobre las respuestas abiertas", 0, 1, "C")
            self.title_added = True 
            self.ln(10)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_comment(self, index, comment, sentiment, problems):
        self.set_font("Arial", "B", 12)
        self.cell(10, 10, f"#{index}:", 0, 0)
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, comment)
        self.ln(2)

        if sentiment.lower() == 'negativo':
            sentiment_color = (255, 0, 0)
        elif sentiment.lower() == 'positivo':
            sentiment_color = (0, 255, 0)
        else:
            sentiment_color = (0, 0, 255)

        self.set_text_color(*sentiment_color)
        self.cell(60, 10, f"        Sentimiento: {sentiment}", 0, 1)
        self.set_text_color(0, 0, 0)
        self.ln(1)

        self.cell(60, 10, f"        Problemas:", 0, 1)
        for problem in problems:
            self.cell(60, 10, f"        - {problem}", 0, 1)
        self.ln(5)

    def add_graphics(self, image_path):
        self.image(image_path, x=10, y=self.get_y() + 10, w=190)
        
def create_pdf(comments, filename):
    pdf = PDF()
    pdf.add_page()

    # Lista para guardar los sentimientos
    sentiments = []

    for index, comment_data in enumerate(comments, start=1):
        comment = comment_data['comment']
        sentiment = comment_data['sentiment']
        problems = comment_data['problems']
        pdf.add_comment(index, comment, sentiment, problems)
        sentiments.append(sentiment)

    # Contar la frecuencia de cada sentimiento
    sentiment_counts = {'Negativo': 0, 'Positivo': 0, 'Neutro': 0}
    for sentiment in sentiments:
        if sentiment.lower() == 'negativo':
            sentiment_counts['Negativo'] += 1
        elif sentiment.lower() == 'positivo':
            sentiment_counts['Positivo'] += 1
        else:
            sentiment_counts['Neutro'] += 1

    # Gráfico de pastel
    plt.figure(figsize=(8, 6))
    plt.pie(sentiment_counts.values(), labels=sentiment_counts.keys(), autopct='%1.1f%%', startangle=140)
    plt.title("Distribución de Sentimientos en el informe")
    plt.savefig("sentimientos.png")
    plt.close()

    # Añadir el gráfico al PDF
    pdf.add_graphics("sentimientos.png")
    
    # Guardar el PDF
    pdf.output(filename)
    print("Informe de ChatGPT PDF creado exitosamente.")

if __name__ == "__main__":
    # Lista de comentarios
    comments = [
            {
        'comment': "Por la pésima experiencia, en la creación de el condominio, mínimo deberíamos tener estacionamiento de visitas.",
        'sentiment': "Negativo",
        'problems': ["Mala experiencia general", "Falta de estacionamiento de visitas"]
    },
    {
        'comment': "El trato no fue el correcto, partiendo por la persona que me atendió para venderme el departamento, además de los problemas del departamento, con fallas y detalles. Además de los nulos estacionamientos de visitas y precios elevados de los estacionamientos.",
        'sentiment': "Negativo",
        'problems': ["Mal trato del personal de ventas", "Fallas en el departamento", "Falta de estacionamientos de visitas", "Precios elevados de estacionamientos"]
    },
    {
        'comment': "Se equivocan en las propuestas entregadas a los bancos, asumimos un aumento del valor, siendo que ellos se equivocaron, además la administración del condominio deja mucho que desear: malos administradores, cobros injustificados, cobros que no deberíamos de asumir nosotros los propietarios y se incluyeron en los gastos comunes, se están agregando modificaciones en el condominio que debería haber sido asumido por la inmobiliaria al momento de la entrega (una multicancha, unos bordes que van en las escaleras, topes de estacionamientos, siendo que no todos los propietarios tenemos estacionamientos).",
        'sentiment': "Negativo",
        'problems': ["Errores en las propuestas bancarias", "Mala administración", "Cobros injustificados", "Cobros incluidos en gastos comunes", "Modificaciones no asumidas por la inmobiliaria"]
    },
    {
        'comment': "Lo único malo es la calidad de las ventanas. No aíslan lo suficientemente el frío y el ruido. Adicionalmente muy mala la elección de administrador.",
        'sentiment': "Negativo",
        'problems': ["Mala calidad de las ventanas", "Mala elección de administrador"]
    },
    {
        'comment': "Muy mala la atención y servicio de garantía.",
        'sentiment': "Negativo",
        'problems': ["Mala atención", "Mal servicio de garantía"]
    },
    {
        'comment': "Por muchas razones y la más importante que a los 2 meses que me entregaron me llovió en la pieza y no han respondido, dan solo soluciones parches.",
        'sentiment': "Negativo",
        'problems': ["Fugas de agua", "Falta de respuesta", "Soluciones temporales"]
    },
    {
        'comment': "Puff millones, partiendo porque tienen un nivel de irresponsabilidad tremenda, tuve que firmar 2 veces mi escritura! Ninguna inmobiliaria seria se atrevería a cometer semejante error, lo mismo mi estacionamiento, está pagado y aún no puedo firmar escritura porque se equivocó no sé quién, no sé cómo no se preocupan de verificar que estas cosas no pasen. Tendré que ir a firmar de nuevo y ni siquiera me avisan, tuve que yo para variar y preguntar qué pasaba por la demora.",
        'sentiment': "Negativo",
        'problems': ["Errores en la firma de escrituras", "Falta de comunicación", "Irresponsabilidad"]
    },
    {
        'comment': "Calidad general.",
        'sentiment': "Neutro",
        'problems': []
    },
    {
        'comment': "Muchas demora, información errada con respecto a los montos del subsidio y nula culpa de parte de la empresa, solo nos dieron la opción de pedir la devolución del dinero, cuando la diferencia eran cerca de 80 USD de diferencia. Ojalá ganarme la giftcard y así compensar el mal rato.",
        'sentiment': "Negativo",
        'problems': ["Demoras", "Información incorrecta sobre subsidios", "Falta de responsabilidad de la empresa"]
    },
    {
        'comment': "Pésima gestión en todas las etapas de adquisición de inmueble. Pésimo trato y servicio de postventa. Pésima calidad de producto entregado. Pésima comunicación con el cliente en relación de resolución de problemas. ¿De verdad tiene cara de mandarme que los evalúe? Jajaja",
        'sentiment': "Negativo",
        'problems': ["Mala gestión", "Mal trato", "Mala calidad del producto", "Mala comunicación"]
    },
    {
        'comment': "Ninguna razón si la recomiendo.",
        'sentiment': "Positivo",
        'problems': []
    },
    {
        'comment': "Proyecto presenta deficiencias. Si bien proceso de compra fue expedito, hay detalles del proyecto que se evidencian de mala calidad.",
        'sentiment': "Negativo",
        'problems': ["Deficiencias del proyecto", "Mala calidad en detalles"]
    },
    {
        'comment': "Ninguna, tuve una espectacular compra, me asesoraron y apoyaron en todo, muy agradecido.",
        'sentiment': "Positivo",
        'problems': []
    },
    {
        'comment': "La recomendaría, pero podrían mejorar el servicio de postventa. Es lento, poco amable.",
        'sentiment': "Neutro",
        'problems': ["Servicio de postventa lento", "Servicio de postventa poco amable"]
    },
    {
        'comment': "Mala calidad de los departamentos, materiales y terminaciones pésimas.",
        'sentiment': "Negativo",
        'problems': ["Mala calidad de departamentos", "Materiales de mala calidad", "Terminaciones pésimas"]
    },
    {
        'comment': "La gestión del personal de venta fue lenta y de muy mala calidad, citándome a firmar en varias ocasiones los mismos documentos por olvido de ellos el no haber firmado alguno y entregando información falsa con respecto al modo de pago del estacionamiento ya que yo pregunte si podía pagarlo con un pie y el resto en cuotas y se me dijo que sí y posteriormente se me informa que no SE PUEDE PAGAR DE ESA MANERA ASÍ COMO UN SINFIN DE FALTA DE GESTIÓN DEL PERSONAL DE VENTA.",
        'sentiment': "Negativo",
        'problems': ["Mala gestión del personal de ventas", "Citaciones repetidas", "Información falsa sobre modo de pago", "Falta de gestión del personal de venta"]
    },
    {
        'comment': "La postventa es muy mala no ayudan ni dan soluciones rápidamente son demasiado malos los ejecutivos a cargo.",
        'sentiment': "Negativo",
        'problems': ["Mala postventa", "Falta de soluciones rápidas", "Malos ejecutivos"]
    },
    {
        'comment': "Pésima atención de postventa, departamento defectuoso.",
        'sentiment': "Negativo",
        'problems': ["Mala atención de postventa", "Departamento defectuoso"]
    },
    {
        'comment': "Compré departamento con subsidio DS19, hicieron algunas cosas muy mal, como no calcular correctamente el monto del subsidio, muchas familias se quedaron sin departamento por este motivo, sin mencionar que los que sí pudimos comprar tuvimos que hacer un sacrificio enorme, no estacionamientos de visita en el condominio, lo cual me parece fatal. Hay errores básicos de construcción como dejar del lado incorrecto la apertura de los ventanales y un par de cosas más.",
        'sentiment': "Negativo",
        'problems': ["Errores en cálculo del subsidio", "Falta de estacionamientos de visita", "Errores básicos de construcción"]
    },
    {
        'comment': "Poca transparencia al vender, se me vendió como Proyecto Marla Central dando a entender que la entrada es por Marla, pero la realidad es que debemos dar toda una vuelta para entrar al condominio, se me dijo también que era la última unidad disponible sin darme la opción de escoger, cuando llegué, me di cuenta que a todos nos dijeron lo mismo, dan mucho espacio a la venta de estacionamiento y poco juegos para niños y áreas verdes, los estacionamientos costosos, la administración de primeras instancias pocas soluciones y muchos problemas, los departamentos defectuosos y no se todo le dan solución, en fin, no muy grata la experiencia de hecho podría continuar, se me debería incluso indemnizar por todos los malos ratos que he pasado.",
        'sentiment': "Negativo",
        'problems': ["Falta de transparencia", "Información falsa", "Problemas de administración", "Departamentos defectuosos"]
    },
    {
        'comment': "Por no responder a fallas que han tenido los departamentos, por no haber respetado el monto de subsidio, por no dar claridad de la entrega total del terreno del proyecto. Por no entregar las instalaciones pulcras.",
        'sentiment': "Negativo",
        'problems': ["Falta de respuesta a fallas", "Incumplimiento del subsidio", "Falta de claridad en la entrega del terreno", "Instalaciones sucias"]
    },
    {
        'comment': "Claro que sí, el servicio de postventa fue muy arbitrario al ser solicitado para reparaciones, en este caso subí la información al portal con evidencias, sin embargo, la persona que visitó mi departamento fue quien finalmente juzgó a su criterio si la reparación procede o no sin tener ningún parámetro más allá que su juicio personal sobre el caso. Por lo demás, en el proceso de compra se nos entregó falsa información sobre la disponibilidad de departamento limitando mi opción de compra a un único departamento, la vendedora me contaba que estaba todo 100% vendido y que el departamento que ella me ofrecía era el último disponible y no tenía otra alternativa... Con el tiempo me da la impresión que eso no era del todo cierto... Hasta la fecha aún hay departamentos disponibles de 1b 1d. Tampoco me dieron la opción de cambiar o algo... Por eso fue mala la experiencia.",
        'sentiment': "Negativo",
        'problems': ["Servicio de postventa arbitrario", "Falsa información sobre disponibilidad de departamentos", "Opciones de compra limitadas"]
    },
    {
        'comment': "Ninguno.",
        'sentiment': "Positivo",
        'problems': ["Ninguno"]
    },
    {
        'comment': "Gestión administrativa, coordinación, tiempo de respuesta a requerimientos, postventa, todo pésimo. Hubo malas gestiones, mala información.",
        'sentiment': "Negativo",
        'problems': ["Mala gestión administrativa", "Mala coordinación", "Tiempos de respuesta largos", "Mala postventa"]
    },
    {
        'comment': "La atención al cliente cuando recién compré fue pésima, el chico que me entregó las llaves no me atendía el teléfono jamás ante mis consultas, se demoran demasiado en las correcciones de postventa, algunos tickets fueron cerrados sin haberles dado solución, la chica rubia teñida que era como jefa de obra o de entrega o algo así era súper pesada y agresiva para hablar, todos los vecinos a los que les pregunté tuvieron el mismo drama con ella, los gastos comunes siguen subiendo excesivamente y no tenemos ascensor, ni siquiera estacionamiento de visita como para justificar algo, llevan meses arreglando el jardín y aún no está listo, los plásticos esos para cerrar el paso se ven horribles, pero como no se avanza con el arreglo no se puede sacar.",
        'sentiment': "Negativo",
        'problems': ["Mala atención al cliente", "Demoras en correcciones de postventa", "Falta de soluciones", "Gastos comunes altos", "Falta de ascensor", "Falta de estacionamiento de visita", "Arreglos del jardín incompletos"]
    },
    {
        'comment': "Lo encuentro que es un buen proyecto.",
        'sentiment': "Positivo",
        'problems': ["Ninguno"]
    },
    {
        'comment': "Por publicidad engañosa ya que el proyecto se llama Marla siendo que en ningún momento tiene salida por Av. Marla ya sea peatonal o por vehículo, cuando compré el departamento me dijeron que el strip iba a tener estos accesos pero después se fue desmintiendo. Los estacionamientos son demasiado caros, prácticamente es el pie para una casa y por otro lado hay algunas terminaciones malas, al primer día se me salió una chapa y la semana me falló un enchufe. Si a futuro tengo la posibilidad de comprarme otro inmueble, no dudaré en no elegirlos.",
        'sentiment': "Negativo",
        'problems': ["Publicidad engañosa", "Estacionamientos caros", "Malas terminaciones"]
    },
    {
        'comment': "Las terminaciones de los departamentos no son las mejores.",
        'sentiment': "Negativo",
        'problems': ["Malas terminaciones"]
    },
    {
        'comment': "Malos materiales, malas terminaciones, las cosas están mal instaladas. Etc.",
        'sentiment': "Negativo",
        'problems': ["Malos materiales", "Malas terminaciones", "Mala instalación"]
    },
    {
        'comment': "El servicio de postventa es muy lento.",
        'sentiment': "Negativo",
        'problems': ["Servicio de postventa lento"]
    },
    {
        'comment': "Todo el proceso de obtención de crédito, no fue lo suficientemente acompañado.",
        'sentiment': "Negativo",
        'problems': ["Falta de acompañamiento en el proceso de obtención de crédito"]
    },
    {
        'comment': "La respuesta de postventa es muy lenta. Con respuesta no me refiero a que respondan un mensaje, sino que una vez resuelto qué hacer, toman mucho tiempo para ejecutar.",
        'sentiment': "Negativo",
        'problems': ["Postventa lenta en ejecución de soluciones"]
    },
    {
        'comment': "Postventa deficiente y materiales de construcción de baja calidad.",
        'sentiment': "Negativo",
        'problems': ["Postventa deficiente", "Materiales de baja calidad"]
    },
    {
        'comment': "Se requiere mejorar el servicio postventa en la atención de las incidencias reportadas.",
        'sentiment': "Neutro",
        'problems': ["Servicio postventa en atención de incidencias"]
    },
    {
        'comment': "No tengo fundamento para no recomendarla, ya que cumple todo lo que ellos muestran, son súper transparentes.",
        'sentiment': "Positivo",
        'problems': ["Ninguno"]
    },
    {
        'comment': "Sería por el motivo que postventa demora mucho en responder y realizar las respectivas reparaciones.",
        'sentiment': "Negativo",
        'problems': ["Postventa lenta en respuestas y reparaciones"]
    },
    {
        'comment': "Porque hubo demasiadas falencias en el proceso de compra, errores por parte de la inmobiliaria, falta a la verdad (nos vendieron un proyecto que tenía salida a Marla y finalmente no fue así). Ni siquiera tiene estacionamientos de visita.",
        'sentiment': "Negativo",
        'problems': ["Falencias en el proceso de compra", "Errores de la inmobiliaria", "Falta de verdad", "Falta de estacionamientos de visita"]
    },
    {
        'comment': "Mala atención al cliente.",
        'sentiment': "Negativo",
        'problems': ["Mala atención al cliente"]
    },
    {
        'comment': "El servicio postventa es muy engorroso. Nadie se hace responsable y solo derivan. Estuve más de seis meses tratando de que me reembolsaran los primeros gastos de servicio de luz, agua y gas. Enviaba correos y no respondían. Cuando tuve un problema con el calefont, no dieron solución siendo que aún estaba vigente la garantía. Tuve que ver por mis propios medios alguna solución.",
        'sentiment': "Negativo",
        'problems': ["Servicio postventa engorroso", "Falta de responsabilidad", "Falta de respuesta", "Falta de solución a problemas bajo garantía"]
    }
    ]
    filename = "Informe_gpt.pdf"
    create_pdf(comments, filename)

# Funcion para unir ambos informes en un pdf
def merge_pdfs(input_pdfs, output_pdf):
    merger = PyPDF2.PdfMerger()

    for pdf in input_pdfs:
        merger.append(pdf)

    merger.write(output_pdf)
    merger.close()

if __name__ == "__main__":
    # Archivos PDF generados
    pdf1 = "Informe_encuesta.pdf"
    pdf2 = "Informe_gpt.pdf"
    pdf_output = "Informe_completo.pdf"

    merge_pdfs([pdf1, pdf2], pdf_output)

    print(f"Archivos PDF combinados y guardados en '{pdf_output}'")