import streamlit as st
import numpy as np
import pandas as pd
from keras.models import load_model
from keras import backend as K
import os
from PIL import Image
import plotly.express as px

# Configuração para compatibilidade
os.environ['TF_USE_LEGACY_KERAS'] = '1'

# Definição de caminhos
MODELSPATH = './models/'
DATAPATH = './data/'

# Dicionário de tipos de lesões traduzido para PT-BR
LESION_TYPE_DICT = {
    0: 'Queratoses actínicas',
    1: 'Carcinoma basocelular',
    2: 'Lesões benignas tipo queratose',
    3: 'Dermatofibroma',
    4: 'Nevos melanocíticos',
    5: 'Melanoma',
    6: 'Lesões vasculares'
}

def render_header():
    """Renderiza o cabeçalho da aplicação"""
    st.write("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-radius: 15px; margin-bottom: 20px;">
            <h1 style="color: white; margin-bottom: 10px; font-size: 2.5rem;">🩺 Doctor Skin</h1>
            <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem; max-width: 800px; margin: 0 auto;">
                Analisador Inteligente de Lesões de Pele com IA
            </p>
        </div>
    """, unsafe_allow_html=True)


@st.cache_data
def load_sample_image():
    """Carrega imagem de exemplo do dataset"""
    try:
        img = Image.open(DATAPATH + '/ISIC_0024312.jpg')
        return img
    except FileNotFoundError:
        st.error("❌ Imagem de exemplo não encontrada. Verifique o caminho do arquivo.")
        return None


@st.cache_data
def preprocess_image(image_path):
    """
    Pré-processa imagem para entrada no modelo
    
    Args:
        image_path: Caminho da imagem ou objeto de upload
        
    Returns:
        Array numpy pré-processado
    """
    try:
        # Abrir e redimensionar imagem
        img = Image.open(image_path).convert('RGB').resize((100, 75))
        
        # Converter para array numpy
        x_test = np.asarray(img).astype('float32')
        
        # Normalização (padronização)
        x_test_mean = np.mean(x_test)
        x_test_std = np.std(x_test)
        x_test = (x_test - x_test_mean) / x_test_std
        
        # Remodelar para formato de entrada do modelo
        x_validate = x_test.reshape(1, 75, 100, 3)
        
        return x_validate
    except Exception as e:
        st.error(f"❌ Erro ao processar imagem: {str(e)}")
        return None


@st.cache_resource
def load_prediction_model():
    """
    Carrega o modelo de predição de câncer de pele
    
    Returns:
        Modelo Keras carregado
    """
    try:
        with st.spinner("🔄 Carregando modelo de inteligência artificial..."):
            # USAR MODELO CORRIGIDO (model_fixed.h5)
            model = load_model(MODELSPATH + 'model_fixed.h5', compile=False)
        st.success("✅ Modelo carregado com sucesso!")
        return model
    except FileNotFoundError:
        st.error(f"❌ Arquivo do modelo não encontrado em: {MODELSPATH}model_fixed.h5")
        st.info("💡 Execute 'python download_pretrained.py' para baixar um modelo funcional")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar modelo: {str(e)}")
        st.info("💡 Dica: Verifique se executou 'python download_pretrained.py' para criar model_fixed.h5")
        return None


@st.cache_data
def predict_skin_lesion(image_array, model):
    """
    Realiza predição do tipo de lesão de pele
    
    Args:
        image_array: Array numpy pré-processado
        model: Modelo Keras carregado
        
    Returns:
        tuple: (probabilidades, classe_predita)
    """
    try:
        # ⚠️ IMPORTANTE: predict_proba NÃO EXISTE no Keras/TensorFlow moderno!
        # predict() já retorna probabilidades quando a última camada usa softmax
        predictions = model.predict(image_array, verbose=0)
        
        # Limpar sessão Keras para liberar memória
        K.clear_session()
        
        # Processar resultados
        probabilities = np.round(predictions[0] * 100, 2).tolist()  # Converter para %
        predicted_class = np.argmax(predictions, axis=1)
        
        K.clear_session()
        
        return probabilities, predicted_class
    except Exception as e:
        st.error(f"❌ Erro durante a predição: {str(e)}")
        return None, None


@st.cache_data
def format_prediction_results(probabilities):
    """
    Formata resultados da predição para exibição
    
    Args:
        probabilities: Lista de probabilidades
        
    Returns:
        DataFrame pandas formatado
    """
    try:
        # Criar DataFrame com resultados
        result = pd.DataFrame({
            'Probabilidade': probabilities
        }, index=np.arange(7))
        
        result = result.reset_index()
        result.columns = ['Classe', 'Probabilidade']
        
        # Mapear classes para nomes em português
        result["Classe"] = result["Classe"].map(LESION_TYPE_DICT)
        
        # Ordenar por probabilidade (decrescente)
        result = result.sort_values('Probabilidade', ascending=False).reset_index(drop=True)
        
        return result
    except Exception as e:
        st.error(f"❌ Erro ao formatar resultados: {str(e)}")
        return None

def display_results_table(result_df):
    """
    Exibe tabela de resultados formatada
    
    Args:
        result_df: DataFrame com resultados
    """
    if result_df is not None:
        # Criar cópia para não modificar o original
        result_df_display = result_df.copy()
        
        # Destacar classe com maior probabilidade
        st.dataframe(
            result_df_display.style.highlight_max(
                subset=['Probabilidade'], 
                color='#4CAF50',
                axis=0
            ).format({'Probabilidade': '{:.2f}%'}),  # Formatação única aqui
            use_container_width=True,
            height=300
        )


def display_probability_chart(result_df):
    """
    Exibe gráfico de barras com probabilidades
    
    Args:
        result_df: DataFrame com resultados
    """
    if result_df is not None:
        # Criar gráfico
        fig = px.bar(
            result_df,
            x="Classe",
            y="Probabilidade",
            color='Classe',
            title="Distribuição das Probabilidades por Tipo de Lesão",
            labels={'Probabilidade': 'Probabilidade (%)', 'Classe': 'Tipo de Lesão'},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        # Configurar layout
        fig.update_layout(
            xaxis_title="Tipo de Lesão",
            yaxis_title="Probabilidade (%)",
            showlegend=False,
            height=450,
            margin=dict(t=50, b=100)
        )
        
        # Rotacionar labels do eixo X para melhor legibilidade
        fig.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)


def sample_data_page():
    """Página de dados de exemplo"""
    st.header("📊 Análise com Imagem de Exemplo")
    
    st.markdown("""
    ### 📌 Sobre esta demonstração
    
    Esta página permite testar o analisador com uma imagem real do dataset ISIC 
    (International Skin Imaging Collaboration).
    
    **Observação importante:** 
    - O modelo atual é pré-treinado (MobileNetV2) para demonstração
    - Para diagnóstico clínico preciso, é necessário re-treinar com dados específicos de lesões de pele
    """)
    
    # Mostrar imagem de exemplo
    if st.checkbox('👁️ Visualizar Imagem de Exemplo'):
        st.info("🖼️ Carregando imagem de exemplo do dataset ISIC...")
        sample_image = load_sample_image()
        
        if sample_image:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(sample_image, caption='Imagem de Exemplo - Dataset ISIC', use_column_width=True)
            
            with col2:
                st.markdown("""
                ### 📋 Detalhes da Imagem
                
                - **Fonte:** ISIC Archive
                - **Tipo:** Lesão de pele real
                - **Dimensões:** 100x75 pixels
                - **Formato:** RGB
                
                Esta imagem é utilizada apenas 
                para demonstração da ferramenta.
                """)
            
            # Carregar modelo e realizar predição
            st.subheader("🧠 Análise com Inteligência Artificial")
            
            if st.button('🚀 Iniciar Análise'):
                model = load_prediction_model()
                
                if model:
                    with st.spinner("⏳ Analisando imagem com IA..."):
                        x_test = preprocess_image(DATAPATH + '/ISIC_0024312.jpg')
                        
                        if x_test is not None:
                            probabilities, predicted_class = predict_skin_lesion(x_test, model)
                            
                            if probabilities is not None:
                                result = format_prediction_results(probabilities)
                                
                                st.subheader("📈 Resultados da Análise")
                                
                                # Resultado principal destacado
                                predicted_lesion = LESION_TYPE_DICT[predicted_class[0]]
                                max_prob = max(probabilities)
                                
                                confidence_level = "Alta" if max_prob > 70 else "Média" if max_prob > 40 else "Baixa"
                                confidence_emoji = "🟢" if max_prob > 70 else "🟡" if max_prob > 40 else "🔴"
                                
                                st.markdown(f"""
                                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3;">
                                    <h3 style="margin: 0; color: #1565c0;">🎯 Resultado Principal</h3>
                                    <p style="font-size: 1.3rem; font-weight: bold; margin: 10px 0; color: #0d47a1;">
                                        {predicted_lesion}
                                    </p>
                                    <p style="margin: 5px 0; color: #546e7a;">
                                        Probabilidade: <strong>{max_prob:.2f}%</strong> 
                                        ({confidence_emoji} Confiança {confidence_level})
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Tabela detalhada
                                st.markdown("### 📊 Detalhamento Completo")
                                display_results_table(result)
                                
                                # Gráfico
                                st.markdown("### 📈 Visualização Gráfica")
                                display_probability_chart(result)
                                
                                # Aviso médico importante
                                st.warning("""
                                ⚠️ **Aviso Médico Importante**
                                
                                Este resultado é **apenas uma análise auxiliar** gerada por inteligência artificial.
                                
                                **NÃO substitui diagnóstico médico profissional.** 
                                
                                🔸 Consulte sempre um dermatologista para avaliação clínica completa
                                🔸 Exames complementares (biópsia, dermatoscopia) podem ser necessários
                                🔸 Esta ferramenta tem fins educacionais e de apoio ao profissional de saúde
                                """)


def upload_image_page():
    """Página de upload de imagem"""
    st.header("📤 Analisar Sua Própria Imagem")
    
    st.markdown("""
    ### 📌 Instruções para Upload
    
    Faça upload de uma imagem de lesão de pele para análise preliminar.
    
    **Recomendações para melhor resultado:**
    - ✅ Imagem nítida e bem iluminada
    - ✅ Foco centralizado na lesão
    - ✅ Fundo neutro e sem sombras
    - ✅ Formatos aceitos: PNG, JPG ou JPEG
    
    ⚠️ **Atenção:** Esta análise é apenas uma ferramenta de apoio. 
    **Sempre consulte um dermatologista para diagnóstico definitivo.**
    """)
    
    # Upload de arquivo
    uploaded_file = st.file_uploader(
        '📁 Selecione uma imagem para análise', 
        type=['png', 'jpg', 'jpeg'],
        help="Suporta arquivos PNG e JPG/JPEG"
    )
    
    if uploaded_file is not None:
        try:
            # Mostrar preview da imagem
            image = Image.open(uploaded_file).convert('RGB')
            st.success("✅ Imagem carregada com sucesso!")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(image, caption='Sua imagem carregada', use_column_width=True)
            
            with col2:
                st.markdown(f"""
                ### 📋 Informações
                
                - **Dimensões:** {image.size[0]} x {image.size[1]} px
                - **Formato:** {image.format}
                - **Modo:** {image.mode}
                """)
            
            # Botão para análise
            st.subheader("🔬 Iniciar Análise com IA")
            
            if st.button('🚀 Analisar Imagem', type="primary", use_container_width=True):
                # Pré-processar imagem
                x_test = preprocess_image(uploaded_file)
                
                if x_test is not None:
                    # Carregar modelo
                    model = load_prediction_model()
                    
                    if model:
                        with st.spinner("⏳ Processando análise com inteligência artificial..."):
                            probabilities, predicted_class = predict_skin_lesion(x_test, model)
                            
                            if probabilities is not None:
                                result = format_prediction_results(probabilities)
                                
                                st.subheader("✅ Análise Concluída")
                                
                                # Resultado principal destacado
                                predicted_lesion = LESION_TYPE_DICT[predicted_class[0]]
                                max_prob = max(probabilities)
                                
                                confidence_level = "Alta" if max_prob > 70 else "Média" if max_prob > 40 else "Baixa"
                                confidence_emoji = "🟢" if max_prob > 70 else "🟡" if max_prob > 40 else "🔴"
                                
                                st.markdown(f"""
                                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 12px; border: 2px solid #4CAF50; margin: 20px 0;">
                                    <h3 style="margin: 0; color: #2e7d32; text-align: center;">🎯 Resultado da Análise</h3>
                                    <p style="font-size: 1.5rem; font-weight: bold; margin: 15px 0; color: #1b5e20; text-align: center;">
                                        {predicted_lesion}
                                    </p>
                                    <p style="text-align: center; font-size: 1.2rem; color: #558b2f; margin: 10px 0;">
                                        Probabilidade: <strong>{max_prob:.2f}%</strong>
                                    </p>
                                    <p style="text-align: center; color: #689f38;">
                                        {confidence_emoji} Nível de confiança: {confidence_level}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Expander com detalhes
                                with st.expander("📋 Ver resultados detalhados de todas as classes"):
                                    display_results_table(result)
                                
                                # Gráfico
                                st.markdown("### 📈 Gráfico de Probabilidades")
                                display_probability_chart(result)
                                
                                # Aviso médico CRÍTICO
                                st.error("""
                                ⚠️ **ATENÇÃO - INFORMAÇÃO MÉDICA IMPORTANTE**
                                
                                **Este resultado NÃO é um diagnóstico médico.**
                                
                                🔸 A inteligência artificial utilizada é uma ferramenta de apoio preliminar
                                🔸 **Consulte obrigatoriamente um dermatologista** para avaliação profissional
                                🔸 Em caso de lesões suspeitas (assimetria, bordas irregulares, cores variadas, diâmetro >6mm, evolução), procure atendimento URGENTE
                                🔸 Esta ferramenta não substitui exames clínicos como dermatoscopia ou biópsia
                                
                                **Sua saúde é importante - não ignore a avaliação de um profissional qualificado!**
                                """)
        
        except Exception as e:
            st.error(f"❌ Erro ao processar imagem: {str(e)}")
            st.info("💡 Dica: Verifique se a imagem está em formato válido (PNG/JPG) e não está corrompida")
    else:
        st.info("ℹ️ Clique no botão acima para fazer upload de uma imagem e iniciar a análise.")


def sidebar_menu():
    """Renderiza menu lateral"""
    st.sidebar.image("https://via.placeholder.com/150x50?text=Doctor+Skin", use_column_width=True)
    st.sidebar.header("🏥 Doctor Skin")
    st.sidebar.markdown("---")
    
    page = st.sidebar.selectbox(
        "📁 Escolha uma opção:",
        ["📊 Imagem de Exemplo", "📤 Minha Própria Imagem"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### ℹ️ Sobre o Projeto
    
    Ferramenta de análise de lesões 
    de pele utilizando inteligência 
    artificial e visão computacional.
    
    ### ⚠️ Responsabilidade
    
    Esta ferramenta é apenas um 
    auxílio preliminar e **não 
    substitui diagnóstico médico**.
    
    ### 🔒 Privacidade
    
    Nenhuma imagem é armazenada 
    ou compartilhada após a análise.
    """)
    
    return page


def main():
    """Função principal da aplicação"""
    
    # Configurações da página
    st.set_page_config(
        page_title="Doctor Skin - Analisador de Lesões de Pele",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Renderizar cabeçalho
    render_header()
    
    # Menu lateral
    page = sidebar_menu()
    
    # Navegação entre páginas
    if page == "📊 Imagem de Exemplo":
        sample_data_page()
    elif page == "📤 Minha Própria Imagem":
        upload_image_page()
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666; font-size: 0.9rem;">
        <p>🩺 Doctor Skin - Ferramenta de Apoio ao Diagnóstico de Lesões de Pele</p>
        <p>⚠️ <strong>Importante:</strong> Esta ferramenta não substitui consulta com dermatologista. 
        Sempre busque orientação médica profissional para diagnóstico e tratamento.</p>
        <p style="font-size: 0.8rem; color: #999; margin-top: 10px;">
            © 2026 Doctor Skin | Desenvolvido com ❤️ para apoio à saúde dermatológica
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()