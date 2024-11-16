import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

data = [
    {'datasetsize': 30000, 'costs_euro': 376},
    {'datasetsize': 15000, 'costs_euro': 236},
    {'datasetsize': 10000, 'costs_euro': 120},
]

dataset_sizes = np.array([entry['datasetsize'] for entry in data]).reshape(-1, 1)
costs = np.array([entry['costs_euro'] for entry in data])

model = LinearRegression()
model.fit(dataset_sizes, costs)

slope = model.coef_[0]
intercept = model.intercept_

function_str = f"Cost Prediction: y = {slope:.4f}x + {intercept:.2f}"

extended_sizes = np.linspace(10000, 50000, 500).reshape(-1, 1) 
predicted_costs = model.predict(extended_sizes)

plt.figure(figsize=(8, 5))
plt.scatter(dataset_sizes, costs, color='blue', s=50, label='Measured Data')
plt.plot(extended_sizes, predicted_costs, color='black', linewidth=1, label='Trend Line')

# titles and labels
plt.title('Azure Costs vs Dataset Size', fontsize=14)
plt.xlabel('Dataset Size (rows)', fontsize=12)
plt.ylabel('Costs (€)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)

# cost prediction function
plt.text(0.95, 0.05, function_str, fontsize=12, color='red', ha='right', va='bottom', transform=plt.gca().transAxes)

plt.tight_layout()
plt.show()
