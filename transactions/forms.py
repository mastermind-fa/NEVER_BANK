from django import forms
from .models import Transaction, UserBankAccount
from .constants import DEPOSIT, TRANSFER
from django import forms
from .models import Transaction



class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account') 
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True 
        self.fields['transaction_type'].widget = forms.HiddenInput() 

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()
    
    
class DepositForm(TransactionForm):
    def clean_amount(self): 
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount
    
class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance 
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance: 
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount
    
    
class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount
    
    


  
class TransferMoneyForm(TransactionForm):
    receiver_account_number = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        self.sender_account = kwargs.pop('sender_account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].initial = TRANSFER

    def clean(self):
        cleaned_data = super().clean()
        receiver_account_number = cleaned_data.get('receiver_account_number')
        amount = cleaned_data.get('amount')

        # Check if receiver account exists
        try:
            receiver_account = UserBankAccount.objects.get(account_no=receiver_account_number)
            self.receiver_account = receiver_account  # This assigns the receiver account to the form instance
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError("Receiver account does not exist")

        # Check sender's balance
        if amount > self.sender_account.balance:
            raise forms.ValidationError("Insufficient balance in your account")

        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")

        return cleaned_data

