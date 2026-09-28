import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from preprocess import load_and_preprocess
from lstm_model import SkillPredictorLSTM
import os

def combined_loss(y_pred, y_true):
    success_pred, time_pred, attempts_pred = y_pred
    
    success_loss = nn.SmoothL1Loss()(success_pred, y_true[:, 0])
    time_loss = nn.SmoothL1Loss()(time_pred, y_true[:, 1])
    att_loss = nn.SmoothL1Loss()(attempts_pred, y_true[:, 2])
    
    loss = 3.0 * success_loss + 5.0 * time_loss + 4.0 * att_loss
    return loss, success_loss, time_loss, att_loss

def train():
    print("Loading data...")
    X_train, y_train, u_train, X_test, y_test, u_test, _, num_users = load_and_preprocess()
    
    # 2. UPDATE DATALOADER
    train_loader = DataLoader(TensorDataset(X_train, y_train, u_train), batch_size=32, shuffle=True)
    test_loader = DataLoader(TensorDataset(X_test, y_test, u_test), batch_size=32)
    
    # 9. MODEL CAPACITY
    model = SkillPredictorLSTM(num_users=num_users, input_size=13, hidden_size=128)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 10. TRAINING RULE: Train full 15 epochs, NO early stopping
    epochs = 15
    best_loss = float('inf')
    
    os.makedirs("app/models", exist_ok=True)
    model_path = "app/models/lstm_model.pt"
    
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        bce_total = 0
        time_total = 0
        att_total = 0
        
        # 7. TRAINING LOOP UPDATE
        for X_b, y_b, u_b in train_loader:
            optimizer.zero_grad()
            y_pred = model(X_b, u_b)
            loss, bce, mse_t, mse_a = combined_loss(y_pred, y_b)
            loss.backward()
            
            optimizer.step()
            
            train_loss += loss.item()
            bce_total += bce.item()
            time_total += mse_t.item()
            att_total += mse_a.item()
            
        n = len(train_loader)
        
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X_b, y_b, u_b in test_loader:
                y_pred = model(X_b, u_b)
                loss, _, _, _ = combined_loss(y_pred, y_b)
                val_loss += loss.item()
        
        val_loss /= len(test_loader)
        
        print(f"Epoch {epoch+1:02d}/{epochs} - "
              f"Loss: {train_loss/n:.4f} "
              f"(Succ: {bce_total/n:.4f}, Time: {time_total/n:.4f}, Att: {att_total/n:.4f}) | "
              f"Val Loss: {val_loss:.4f}")
              
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), model_path)
            
    print(f"Training complete. Best model saved to {model_path}")

if __name__ == "__main__":
    train()
