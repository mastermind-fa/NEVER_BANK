from django.contrib import admin

# from transactions.models import Transaction
from .models import Transaction
from .views import send_mail


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'loan_approve']
    
    def save_model(self, request, obj, form, change):
        obj.account.balance += obj.amount
        obj.balance_after_transaction = obj.account.balance
        obj.account.save()
        send_mail(
            obj.account.user,
            obj.account.user.email,
            obj.amount,
            'Loan Approval',
            'transactions/admin_mail.html')
        super().save_model(request, obj, form, change)
