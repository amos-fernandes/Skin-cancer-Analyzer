# download_pretrained.py
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

print("Baixando MobileNetV2 pré-treinado...")
base_model = MobileNetV2(
    input_shape=(75, 100, 3),
    include_top=False,
    weights='imagenet'
)

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(7, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.save('./models/model_fixed.h5')

print("✅ Modelo pré-treinado salvo em ./models/model_fixed.h5")
print("💡 Use este modelo para demonstração até re-treinar com dados reais")