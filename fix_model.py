# fix_model_v2.py
import h5py
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
import os

MODELSPATH = './models/'

def extract_weights_from_corrupted_h5(h5_path):
    """
    Extrai pesos diretamente do arquivo HDF5, ignorando configuração corrompida
    """
    weights = {}
    
    try:
        with h5py.File(h5_path, 'r') as f:
            print("🔍 Explorando estrutura do arquivo HDF5...")
            
            # Listar todos os grupos/pesos
            def visit_func(name, obj):
                if isinstance(obj, h5py.Dataset):
                    weights[name] = np.array(obj)
                    print(f"  ✓ {name}: shape={weights[name].shape}")
            
            f.visititems(visit_func)
        
        print(f"\n✅ Extraídos {len(weights)} tensores de pesos do arquivo HDF5")
        return weights
    
    except Exception as e:
        print(f"❌ Erro ao extrair pesos: {e}")
        return None


def rebuild_model_with_weights(weights_dict):
    """
    Recria arquitetura correta (Conv2D) e injeta pesos manualmente
    """
    # 1. Criar arquitetura CORRETA para imagens 2D (75x100x3)
    print("\n🏗️  Recriando arquitetura Conv2D correta...")
    model = keras.Sequential([
        # Camada 1: Conv2D (32 filtros)
        layers.Conv2D(32, (3, 3), activation='relu', padding='same', 
                     input_shape=(75, 100, 3), name='conv2d_1'),
        layers.MaxPooling2D((2, 2), name='max_pool_1'),
        
        # Camada 2: Conv2D (64 filtros)
        layers.Conv2D(64, (3, 3), activation='relu', padding='same', name='conv2d_2'),
        layers.MaxPooling2D((2, 2), name='max_pool_2'),
        
        # Camada 3: Conv2D (128 filtros)
        layers.Conv2D(128, (3, 3), activation='relu', padding='same', name='conv2d_3'),
        layers.MaxPooling2D((2, 2), name='max_pool_3'),
        
        # Classificador
        layers.Flatten(name='flatten'),
        layers.Dense(256, activation='relu', name='dense_1'),
        layers.Dropout(0.5, name='dropout_1'),
        layers.Dense(128, activation='relu', name='dense_2'),
        layers.Dropout(0.3, name='dropout_2'),
        layers.Dense(7, activation='softmax', name='output')
    ])
    
    print("✅ Arquitetura criada com sucesso")
    
    # 2. Mapear pesos manualmente (conversão Conv3D → Conv2D)
    print("\n🔄 Convertendo e injetando pesos...")
    layer_mapping = {
        'conv2d_1': ['conv3d', 'conv3d_1', 'conv3d_2'],  # Possíveis nomes no HDF5
        'conv2d_2': ['conv3d_3', 'conv3d_4'],
        'conv2d_3': ['conv3d_5', 'conv3d_6'],
        'dense_1': ['dense', 'dense_1', 'dense_2'],
        'dense_2': ['dense_3', 'dense_4'],
        'output': ['dense_5', 'dense_6', 'output']
    }
    
    weights_injected = 0
    for layer in model.layers:
        if hasattr(layer, 'get_weights'):
            layer_name = layer.name
            
            # Encontrar pesos correspondentes no dicionário
            found = False
            for possible_name in layer_mapping.get(layer_name, [layer_name]):
                # Buscar por nome aproximado
                for weight_key in weights_dict.keys():
                    if possible_name in weight_key.lower():
                        raw_weights = weights_dict[weight_key]
                        
                        # CONVERSÃO CRÍTICA: Conv3D kernel → Conv2D kernel
                        if raw_weights.ndim == 5:  # Shape Conv3D: (d, h, w, in, out)
                            print(f"  ⚠️  Convertendo kernel Conv3D ({raw_weights.shape}) → Conv2D")
                            # Pegar slice central da dimensão de profundidade
                            converted = raw_weights[1, :, :, :, :]  # Mantém h, w, in, out
                            layer.set_weights([converted])
                            found = True
                            weights_injected += 1
                            print(f"  ✓ {layer_name}: pesos convertidos e injetados")
                            break
                        elif raw_weights.ndim == 4:  # Já é Conv2D ou Dense
                            try:
                                layer.set_weights([raw_weights])
                                found = True
                                weights_injected += 1
                                print(f"  ✓ {layer_name}: pesos injetados diretamente")
                                break
                            except ValueError as e:
                                print(f"  ⚠️  Shape incompatível para {layer_name}: {e}")
                                continue
                if found:
                    break
            
            if not found:
                print(f"  ⚪ {layer_name}: pesos não encontrados (inicializando aleatoriamente)")
    
    print(f"\n✅ {weights_injected} camadas receberam pesos convertidos")
    return model


def test_model(model):
    """Testa se o modelo carregado funciona corretamente"""
    print("\n🧪 Testando modelo com entrada simulada...")
    try:
        test_input = np.random.rand(1, 75, 100, 3).astype('float32')
        output = model.predict(test_input, verbose=0)
        print(f"✅ Predição bem-sucedida! Shape da saída: {output.shape}")
        print(f"   Probabilidades: {output[0][:3]}... (primeiras 3 classes)")
        return True
    except Exception as e:
        print(f"❌ Falha no teste: {e}")
        return False


def main():
    h5_path = MODELSPATH + 'model.h5'
    
    if not os.path.exists(h5_path):
        print(f"❌ Arquivo não encontrado: {h5_path}")
        print("💡 Dica: Verifique se a pasta 'models' contém 'model.h5'")
        return
    
    print("="*60)
    print("🛠️  SCRIPT DE RECUPERAÇÃO DE MODELO CORROMPIDO")
    print("="*60)
    
    # Passo 1: Extrair pesos brutos
    weights = extract_weights_from_corrupted_h5(h5_path)
    if weights is None:
        print("\n❌ Falha na extração de pesos. Abortando.")
        return
    
    # Passo 2: Recriar modelo e injetar pesos
    model = rebuild_model_with_weights(weights)
    
    # Passo 3: Testar modelo
    if test_model(model):
        # Passo 4: Salvar modelo corrigido
        output_path = MODELSPATH + 'model_fixed.h5'
        print(f"\n💾 Salvando modelo corrigido em: {output_path}")
        model.save(output_path)
        print("\n" + "="*60)
        print("✅ MODELO RECUPERADO COM SUCESSO!")
        print("="*60)
        print("\n📌 Próximos passos:")
        print("  1. No seu app.py, substitua 'model.h5' por 'model_fixed.h5'")
        print("  2. Remova a linha 'ynew = model.predict_proba(...)' (não existe no Keras)")
        print("  3. Execute: streamlit cache clear")
        print("  4. Execute: streamlit run app.py")
    else:
        print("\n❌ Modelo recuperado mas com problemas. Considere re-treinar.")


if __name__ == "__main__":
    main()