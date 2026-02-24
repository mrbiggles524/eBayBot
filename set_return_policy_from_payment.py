"""
Set return policy ID based on payment policy ID pattern.
"""
import re

def main():
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get payment policy ID
        payment_match = re.search(r'PAYMENT_POLICY_ID=(\d+)', content)
        if payment_match:
            payment_id = payment_match.group(1)
            return_id = str(int(payment_id) + 1)
            
            # Update return policy
            pattern = r'RETURN_POLICY_ID=.*'
            replacement = f'RETURN_POLICY_ID={return_id}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
            else:
                content += f"\nRETURN_POLICY_ID={return_id}\n"
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Set RETURN_POLICY_ID to {return_id} (payment policy {payment_id} + 1)")
            print("This is a guess - it may not work, but worth trying.")
        else:
            print("Could not find PAYMENT_POLICY_ID in .env")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
