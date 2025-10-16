"""
Fetch CRM Data and Prepare for ML Training - FIXED VERSION
app/ml/training/fetch_and_prepare_data.py

This script:
1. Fetches customers, payments, and tickets from Habari CRM API
2. Prepares features for ML training
3. Handles missing/empty data gracefully
4. Saves processed data for model training
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app import create_app
from app.extensions import db
from app.models.company import Company


class CRMDataFetcher:
    """Fetch and prepare data from Habari CRM API"""
    
    def __init__(self, base_url: str):
        """
        Initialize data fetcher
        
        Args:
            base_url: Base URL of CRM API
        """
        self.base_url = base_url
        self.timeout = 30
        
    def fetch_table(self, table_name: str) -> list:
        """
        Fetch data from a specific table
        
        Args:
            table_name: Name of table (customers, payments, tickects)
            
        Returns:
            List of records
        """
        try:
            url = f"{self.base_url}?table={table_name}&limit=10"
            print(f"📡 Fetching {table_name} from: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                # Check for error
                if 'error' in data:
                    print(f"⚠️  API returned error: {data.get('error')}")
                    return []
                    
                if 'data' in data:
                    records = data['data']
                elif 'records' in data:
                    records = data['records']
                else:
                    records = [data]
            elif isinstance(data, list):
                records = data
            else:
                print(f"⚠️  Unexpected response format for {table_name}")
                return []
            
            print(f"✅ Fetched {len(records)} {table_name}")
            return records
            
        except requests.exceptions.Timeout:
            print(f"❌ Timeout fetching {table_name}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {table_name}: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response for {table_name}: {e}")
            return []
    
    def fetch_all_data(self) -> dict:
        """
        Fetch all data from CRM
        
        Returns:
            Dictionary with customers, payments, and tickets
        """
        print("\n" + "="*60)
        print("FETCHING CRM DATA")
        print("="*60)
        
        data = {
            'customers': self.fetch_table('customers'),
            'payments': self.fetch_table('payments'),
            'tickets': self.fetch_table('tickets')  # Note: API uses 'Tickects' spelling
        }
        
        print("\n📊 Data Summary:")
        print(f"   Customers: {len(data['customers'])}")
        print(f"   Payments:  {len(data['payments'])}")
        print(f"   Tickets:   {len(data['tickets'])}")
        
        return data


class MLDataPreparator:
    """Prepare CRM data for ML training"""
    
    def __init__(self, crm_data: dict):
        """
        Initialize preparator
        
        Args:
            crm_data: Dictionary with customers, payments, tickets
        """
        self.crm_data = crm_data
        self.customers_df = None
        self.payments_df = None
        self.tickets_df = None
        self.training_df = None
        
    def prepare_dataframes(self):
        """Convert raw data to pandas DataFrames"""
        print("\n" + "="*60)
        print("PREPARING DATAFRAMES")
        print("="*60)
        
        # Customers
        if self.crm_data['customers']:
            self.customers_df = pd.DataFrame(self.crm_data['customers'])
            print(f"✅ Customers DataFrame: {self.customers_df.shape}")
            print(f"   Columns: {list(self.customers_df.columns)}")
            
            # CRITICAL FIX: Filter to only include diverse customer states
            # Check if we have active customers
            status_col = self._find_column(self.customers_df, ['status', 'connection_status'])
            if status_col:
                # Count active vs inactive
                status_counts = self.customers_df[status_col].astype(str).value_counts()
                print(f"\n📊 Customer Status Distribution:")
                for status, count in status_counts.head(10).items():
                    print(f"   {status}: {count}")
                
                # Only filter if we have SOME active customers
                active_values = ['active', 'connected', '1', 'true', 'Active', 'Connected']
                has_active = self.customers_df[status_col].astype(str).isin(active_values).any()
                
                if has_active:
                    # Include both active AND recently inactive customers for training
                    # This gives us variation in the target variable
                    print(f"\n🔍 Filtering to include active and recently churned customers...")
                    
                    # Keep: Active customers + customers with recent disconnection dates
                    is_active = self.customers_df[status_col].astype(str).isin(active_values)
                    
                    # Also keep recently disconnected (last 6 months)
                    disconnect_col = self._find_column(self.customers_df, ['disconnection_date', 'churned_date'])
                    if disconnect_col:
                        self.customers_df['disconnect_dt'] = pd.to_datetime(
                            self.customers_df[disconnect_col], 
                            errors='coerce'
                        )
                        recent_disconnect = (
                            (datetime.now() - self.customers_df['disconnect_dt']).dt.days < 180
                        ) & pd.notna(self.customers_df['disconnect_dt'])
                        
                        # Keep active OR recently disconnected
                        keep_mask = is_active | recent_disconnect
                    else:
                        keep_mask = is_active
                    
                    original_count = len(self.customers_df)
                    self.customers_df = self.customers_df[keep_mask].copy()
                    filtered_count = len(self.customers_df)
                    
                    print(f"   Original: {original_count} customers")
                    print(f"   Filtered: {filtered_count} customers ({filtered_count/original_count*100:.1f}%)")
                    print(f"   Removed: {original_count - filtered_count} (all disconnected/inactive)")
                    
                    if filtered_count == 0:
                        print("\n❌ No active or recently churned customers found!")
                        print("   Cannot train model with only one class")
                        return False
                else:
                    print(f"\n⚠️  No active customers found in dataset")
                    print(f"   All customers appear to be inactive/disconnected")
                    print(f"   Cannot train a churn prediction model")
                    return False
        else:
            print("⚠️  No customer data available")
            return False
        
        # Payments
        if self.crm_data['payments'] and not (len(self.crm_data['payments']) == 1 and 'error' in self.crm_data['payments'][0]):
            self.payments_df = pd.DataFrame(self.crm_data['payments'])
            print(f"✅ Payments DataFrame: {self.payments_df.shape}")
            print(f"   Columns: {list(self.payments_df.columns)}")
        else:
            print("⚠️  No payment data available")
            self.payments_df = pd.DataFrame()
        
        # Tickets
        if self.crm_data['tickets'] and not (len(self.crm_data['tickets']) == 1 and 'error' in self.crm_data['tickets'][0]):
            self.tickets_df = pd.DataFrame(self.crm_data['tickets'])
            print(f"✅ Tickets DataFrame: {self.tickets_df.shape}")
            print(f"   Columns: {list(self.tickets_df.columns)}")
        else:
            print("⚠️  No ticket data available")
            self.tickets_df = pd.DataFrame()
        
        return True
    
    def engineer_features(self):
        """Engineer features from CRM data"""
        print("\n" + "="*60)
        print("ENGINEERING FEATURES")
        print("="*60)
        
        # Start with customers
        df = self.customers_df.copy()
        
        # Map customer_id (ensure it's a string for merging)
        customer_id_col = self._find_id_column(df, ['id', 'customer_id', 'customerId'])
        if not customer_id_col:
            print("❌ Cannot find customer ID column")
            return False
        
        print(f"📝 Using customer ID column: {customer_id_col}")
        df['customer_id'] = df[customer_id_col].astype(str)
        
        # === PAYMENT FEATURES ===
        if not self.payments_df.empty:
            print("\n💰 Engineering payment features...")
            
            # Ensure customer_id exists in payments
            payment_cust_col = self._find_id_column(
                self.payments_df, 
                ['customer_id', 'customerId', 'cust_id', 'id']
            )
            
            if payment_cust_col:
                payments = self.payments_df.copy()
                payments['customer_id'] = payments[payment_cust_col].astype(str)
                
                # Aggregate payment metrics per customer
                payment_agg = payments.groupby('customer_id').agg({
                    payment_cust_col: 'count',  # total_payments
                }).reset_index()
                payment_agg.columns = ['customer_id', 'total_payments']
                
                # Amount column
                amount_col = self._find_column(payments, ['amount', 'payment_amount', 'total'])
                if amount_col:
                    payments['amount_numeric'] = pd.to_numeric(payments[amount_col], errors='coerce')
                    payment_amount = payments.groupby('customer_id')['amount_numeric'].agg([
                        ('total_payment_amount', 'sum'),
                        ('avg_payment_amount', 'mean')
                    ]).reset_index()
                    payment_agg = payment_agg.merge(payment_amount, on='customer_id', how='left')
                
                # Payment date - calculate recency
                date_col = self._find_column(payments, ['date', 'payment_date', 'created_at'])
                if date_col:
                    payments['payment_date'] = pd.to_datetime(payments[date_col], errors='coerce')
                    last_payment = payments.groupby('customer_id')['payment_date'].max().reset_index()
                    last_payment.columns = ['customer_id', 'last_payment_date']
                    
                    # Calculate days since last payment
                    last_payment['days_since_last_payment'] = (
                        datetime.now() - last_payment['last_payment_date']
                    ).dt.days
                    
                    payment_agg = payment_agg.merge(
                        last_payment[['customer_id', 'days_since_last_payment']], 
                        on='customer_id', 
                        how='left'
                    )
                
                # Merge with main dataframe
                df = df.merge(payment_agg, on='customer_id', how='left')
                print(f"   ✅ Added {len(payment_agg.columns)-1} payment features")
            else:
                print("   ⚠️  Cannot link payments to customers (no matching ID column)")
        else:
            print("\n💰 No payment data - creating default payment features...")
            # Create default payment features (all zeros)
            df['total_payments'] = 0
            df['total_payment_amount'] = 0.0
            df['avg_payment_amount'] = 0.0
            df['days_since_last_payment'] = 999  # Very high number = no payments
        
        # === TICKET FEATURES ===
        if not self.tickets_df.empty:
            print("\n🎫 Engineering ticket features...")
            
            # Ensure customer_id exists in tickets
            ticket_cust_col = self._find_id_column(
                self.tickets_df,
                ['customer_id', 'customerId', 'cust_id', 'id']
            )
            
            if ticket_cust_col:
                tickets = self.tickets_df.copy()
                tickets['customer_id'] = tickets[ticket_cust_col].astype(str)
                
                # Aggregate ticket metrics per customer
                ticket_agg = tickets.groupby('customer_id').agg({
                    ticket_cust_col: 'count',  # total_tickets
                }).reset_index()
                ticket_agg.columns = ['customer_id', 'total_tickets']
                
                # Status column
                status_col = self._find_column(tickets, ['status', 'ticket_status'])
                if status_col:
                    # Count open tickets
                    tickets['is_open'] = tickets[status_col].astype(str).str.lower().isin(['open', 'pending', 'in_progress'])
                    open_tickets = tickets.groupby('customer_id')['is_open'].sum().reset_index()
                    open_tickets.columns = ['customer_id', 'open_tickets']
                    ticket_agg = ticket_agg.merge(open_tickets, on='customer_id', how='left')
                
                # Priority column
                priority_col = self._find_column(tickets, ['priority', 'ticket_priority'])
                if priority_col:
                    tickets['is_high_priority'] = tickets[priority_col].astype(str).str.lower().isin(['high', 'urgent', 'critical'])
                    high_priority = tickets.groupby('customer_id')['is_high_priority'].sum().reset_index()
                    high_priority.columns = ['customer_id', 'high_priority_tickets']
                    ticket_agg = ticket_agg.merge(high_priority, on='customer_id', how='left')
                
                # Ticket date - calculate recency
                date_col = self._find_column(tickets, ['date', 'created_at', 'ticket_date'])
                if date_col:
                    tickets['ticket_date'] = pd.to_datetime(tickets[date_col], errors='coerce')
                    last_ticket = tickets.groupby('customer_id')['ticket_date'].max().reset_index()
                    last_ticket.columns = ['customer_id', 'last_ticket_date']
                    
                    # Calculate days since last ticket
                    last_ticket['days_since_last_ticket'] = (
                        datetime.now() - last_ticket['last_ticket_date']
                    ).dt.days
                    
                    ticket_agg = ticket_agg.merge(
                        last_ticket[['customer_id', 'days_since_last_ticket']],
                        on='customer_id',
                        how='left'
                    )
                
                # Merge with main dataframe
                df = df.merge(ticket_agg, on='customer_id', how='left')
                print(f"   ✅ Added {len(ticket_agg.columns)-1} ticket features")
            else:
                print("   ⚠️  Cannot link tickets to customers (no matching ID column)")
        else:
            print("\n🎫 No ticket data - creating default ticket features...")
            # Create default ticket features (all zeros)
            df['total_tickets'] = 0
            df['open_tickets'] = 0
            df['high_priority_tickets'] = 0
            df['days_since_last_ticket'] = 999  # Very high number = no tickets
        
        # === CUSTOMER FEATURES ===
        print("\n👤 Engineering customer features...")
        
        # Signup/registration date - calculate tenure
        date_col = self._find_column(df, ['signup_date', 'registration_date', 'created_at', 'date_joined', 'date_installed'])
        if date_col:
            df['signup_date'] = pd.to_datetime(df[date_col], errors='coerce')
            df['tenure_days'] = (datetime.now() - df['signup_date']).dt.days
            df['tenure_months'] = (df['tenure_days'] / 30).astype(int)
            # Fix negative tenures
            df.loc[df['tenure_months'] < 0, 'tenure_months'] = 0
            print(f"   ✅ Calculated tenure from {date_col}")
        else:
            print("   ⚠️  No signup date found, setting default tenure")
            df['tenure_months'] = 12  # Default
        
        # Account status - FIXED: convert to string first
        status_col = self._find_column(df, ['status', 'account_status', 'customer_status', 'connection_status'])
        if status_col:
            # Convert to string first to avoid AttributeError
            df['is_active'] = df[status_col].astype(str).str.lower().isin(['active', 'connected', '1', 'true'])
            print(f"   ✅ Mapped account status from {status_col}")
        else:
            df['is_active'] = True  # Default
        
        # Customer balance (if available)
        balance_col = self._find_column(df, ['balance', 'customer_balance', 'outstanding_balance'])
        if balance_col:
            df['balance_amount'] = pd.to_numeric(df[balance_col], errors='coerce').fillna(0)
            print(f"   ✅ Added balance from {balance_col}")
        
        # Fill missing values with 0 for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        # Create derived features
        print("\n🔧 Creating derived features...")
        
        # Payment frequency (payments per month)
        if 'total_payments' in df.columns and 'tenure_months' in df.columns:
            df['payment_frequency'] = df['total_payments'] / (df['tenure_months'] + 1)
        
        # Ticket frequency (tickets per month)
        if 'total_tickets' in df.columns and 'tenure_months' in df.columns:
            df['ticket_frequency'] = df['total_tickets'] / (df['tenure_months'] + 1)
        
        # Average payment per month
        if 'total_payment_amount' in df.columns and 'tenure_months' in df.columns:
            df['avg_monthly_payment'] = df['total_payment_amount'] / (df['tenure_months'] + 1)
        
        # Support engagement ratio
        if 'total_tickets' in df.columns and 'total_payments' in df.columns:
            df['support_engagement_ratio'] = df['total_tickets'] / (df['total_payments'] + 1)
        
        self.training_df = df
        
        print("\n✅ Feature engineering complete!")
        print(f"   Final shape: {df.shape}")
        print(f"   Features: {len([c for c in df.columns if c not in ['customer_id', 'customer_name']])} (excluding ID/name)")
        
        return True
    
    def create_target_variable(self):
        """
        Create churn target variable based on business rules
        
        For customers WITHOUT payment/ticket data, we rely on:
        1. Account status (active vs inactive)
        2. Disconnection date
        3. Balance information
        4. Connection status
        """
        print("\n" + "="*60)
        print("CREATING TARGET VARIABLE (CHURN)")
        print("="*60)
        
        df = self.training_df
        
        # Initialize churn score
        df['churn_score'] = 0
        
        # CRITICAL: Check if we have payment/ticket data
        has_payment_data = 'total_payments' in df.columns and df['total_payments'].sum() > 0
        has_ticket_data = 'total_tickets' in df.columns and df['total_tickets'].sum() > 0
        
        print(f"\n📊 Data availability:")
        print(f"   Payment data: {'YES' if has_payment_data else 'NO'}")
        print(f"   Ticket data: {'YES' if has_ticket_data else 'NO'}")
        
        if has_payment_data or has_ticket_data:
            # Use payment/ticket-based rules
            print("\n🔍 Using payment/ticket-based churn rules...")
            
            # Rule 1: No recent payment (60+ days)
            if has_payment_data and 'days_since_last_payment' in df.columns:
                df['churn_score'] += ((df['days_since_last_payment'] > 60) & (df['days_since_last_payment'] < 999)).astype(int) * 2
                print("✅ Added payment recency rule")
            
            # Rule 2: High ticket frequency
            if has_ticket_data and 'ticket_frequency' in df.columns:
                high_ticket_threshold = df['ticket_frequency'].quantile(0.75)
                df['churn_score'] += (df['ticket_frequency'] > high_ticket_threshold).astype(int)
                print("✅ Added high ticket frequency rule")
            
            # Rule 3: Many open tickets
            if has_ticket_data and 'open_tickets' in df.columns:
                df['churn_score'] += (df['open_tickets'] >= 2).astype(int)
                print("✅ Added open tickets rule")
            
            # Rule 4: Account inactive
            if 'is_active' in df.columns:
                df['churn_score'] += (~df['is_active']).astype(int) * 2
                print("✅ Added account status rule")
            
            # Rule 5: Low payment activity
            if has_payment_data and 'payment_frequency' in df.columns:
                low_payment_threshold = df['payment_frequency'].quantile(0.25)
                df['churn_score'] += ((df['payment_frequency'] < low_payment_threshold) & (df['payment_frequency'] > 0)).astype(int)
                print("✅ Added low payment frequency rule")
            
            # Threshold
            df['churned'] = (df['churn_score'] >= 2).astype(int)
            
        else:
            # NO payment/ticket data - use customer attributes only
            print("\n🔍 Using customer-attribute-based churn rules (no payment/ticket data)...")
            
            # Rule 1: Account is explicitly inactive/disconnected - STRONG
            if 'is_active' in df.columns:
                # Account marked as inactive
                inactive_mask = ~df['is_active']
                df.loc[inactive_mask, 'churn_score'] += 3
                print(f"✅ Account inactive rule: {inactive_mask.sum()} customers")
            
            # Rule 2: Has disconnection date - STRONG
            disconnection_col = self._find_column(df, ['disconnection_date', 'churned_date', 'disconnect_date'])
            if disconnection_col:
                has_disconnect = pd.notna(df[disconnection_col]) & (df[disconnection_col] != '') & (df[disconnection_col] != '0000-00-00')
                df.loc[has_disconnect, 'churn_score'] += 3
                print(f"✅ Has disconnection date rule: {has_disconnect.sum()} customers")
            
            # Rule 3: Connection status shows disconnected
            connection_col = self._find_column(df, ['connection_status', 'status'])
            if connection_col:
                disconnected = df[connection_col].astype(str).str.lower().isin(['disconnected', 'inactive', 'suspended', 'cancelled', 'terminated'])
                df.loc[disconnected, 'churn_score'] += 3
                print(f"✅ Connection status disconnected rule: {disconnected.sum()} customers")
            
            # Rule 4: Large negative balance (owes money, not paying)
            if 'balance_amount' in df.columns:
                large_debt = df['balance_amount'] < -1000
                df.loc[large_debt, 'churn_score'] += 1
                print(f"✅ Large debt rule: {large_debt.sum()} customers")
            
            # Rule 5: Very old tenure but never reconnected (dormant)
            if 'tenure_months' in df.columns:
                very_old = df['tenure_months'] > 36  # 3+ years
                df.loc[very_old, 'churn_score'] += 1
                print(f"✅ Dormant account rule: {very_old.sum()} customers")
            
            # More conservative threshold when using attribute-based rules
            # Need at least score of 3 (i.e., one strong indicator)
            df['churned'] = (df['churn_score'] >= 3).astype(int)
        
        churn_count = df['churned'].sum()
        churn_rate = (churn_count / len(df)) * 100 if len(df) > 0 else 0
        
        print(f"\n📊 Target Variable Summary:")
        print(f"   Total customers: {len(df)}")
        print(f"   Churned: {churn_count} ({churn_rate:.1f}%)")
        print(f"   Active: {len(df) - churn_count} ({100-churn_rate:.1f}%)")
        
        if churn_rate < 5:
            print(f"\n⚠️  WARNING: Low churn rate ({churn_rate:.1f}%)")
            print("   Model may have limited learning signal")
        elif churn_rate > 95:
            print(f"\n⚠️  WARNING: Very high churn rate ({churn_rate:.1f}%)")
            print("   Most customers marked as churned")
            print("   This happens when:")
            print("   - No payment/ticket data available")
            print("   - Most accounts are inactive/disconnected")
            print("   Consider: Filter to only active customers for training")
        
        self.training_df = df
        return True
    
    def save_training_data(self, output_path: str):
        """Save prepared data to CSV"""
        print("\n" + "="*60)
        print("SAVING TRAINING DATA")
        print("="*60)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        self.training_df.to_csv(output_path, index=False)
        
        print(f"✅ Saved to: {output_path}")
        print(f"   Shape: {self.training_df.shape}")
        print(f"   Features: {len(self.training_df.columns)}")
        
        # Save column info
        info_path = output_path.replace('.csv', '_info.txt')
        with open(info_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("TRAINING DATA INFO\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total Rows: {len(self.training_df)}\n")
            f.write(f"Total Columns: {len(self.training_df.columns)}\n\n")
            f.write(f"Churn Rate: {(self.training_df['churned'].sum() / len(self.training_df) * 100):.1f}%\n\n")
            f.write("Columns:\n")
            for col in self.training_df.columns:
                dtype = self.training_df[col].dtype
                nulls = self.training_df[col].isnull().sum()
                unique = self.training_df[col].nunique()
                f.write(f"  - {col:40s} ({str(dtype):10s}) - {nulls:5d} nulls, {unique:6d} unique\n")
        
        print(f"✅ Saved column info to: {info_path}")
        
        return output_path
    
    # Helper methods
    def _find_column(self, df, possible_names):
        """Find column that matches possible names (case-insensitive)"""
        df_cols_lower = {col.lower(): col for col in df.columns}
        for name in possible_names:
            if name.lower() in df_cols_lower:
                return df_cols_lower[name.lower()]
        return None
    
    def _find_id_column(self, df, possible_names):
        """Find ID column"""
        return self._find_column(df, possible_names)


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("HABARI CRM DATA PREPARATION FOR ML")
    print("="*60)
    
    # CRM API URL
    CRM_API_URL = "https://palegreen-porpoise-596991.hostingersite.com/Web_CRM/api.php"
    
    # Output path
    output_path = "app/ml/data/training_data.csv"
    
    # Step 1: Fetch data
    fetcher = CRMDataFetcher(CRM_API_URL)
    crm_data = fetcher.fetch_all_data()
    
    if not crm_data['customers']:
        print("\n❌ No customer data available. Cannot proceed.")
        return False
    
    # Step 2: Prepare data
    preparator = MLDataPreparator(crm_data)
    
    if not preparator.prepare_dataframes():
        print("\n❌ Failed to prepare dataframes")
        return False
    
    if not preparator.engineer_features():
        print("\n❌ Failed to engineer features")
        return False
    
    if not preparator.create_target_variable():
        print("\n❌ Failed to create target variable")
        return False
    
    # Step 3: Save data
    output_file = preparator.save_training_data(output_path)
    
    print("\n" + "="*60)
    print("✅ DATA PREPARATION COMPLETE!")
    print("="*60)
    print(f"\n📁 Training data saved to: {output_file}")
    print(f"\n🚀 Next step: Train the model")
    print(f"   python app/ml/training/train_model.py --data-file {output_file}")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)