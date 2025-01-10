from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from transactions.constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID, TRANSFER
from datetime import datetime
from django.db.models import Sum
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
    TransferMoneyForm
)
from transactions.models import Transaction
from django.shortcuts import render
from accounts.models import UserBankAccount
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
def send_mail(user, to_user, amount, mail_subject, template):
    
    message = render_to_string(template, {
        'user': user,
        'amount': amount,
    })
    to_email = to_user
    send_email = EmailMultiAlternatives(mail_subject, '', to=[to_user])
    send_email.attach_alternative(message, "text/html")
    send_email.send()
    
def send_transfer_mail(user, receiver, to_user, amount, mail_subject, template):
    message = render_to_string(template, {
        'user': user,
        'receiver': receiver,	
        'amount': amount,
    })
    to_email = to_user
    send_email = EmailMultiAlternatives(mail_subject, '', to=[to_user])
    send_email.attach_alternative(message, "text/html")
    send_email.send()
    
    


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context.update({
            'title': self.title
        })

        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        
        account.balance += amount 
        account.save(
            update_fields=[
                'balance'
            ]
        )

        
        send_mail(self.request.user, self.request.user.email, amount, 'Deposit Money', 'transactions/deposit_mail.html')
        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        total_bank_balance = UserBankAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0
        if total_bank_balance < amount:
            
            messages.error(self.request, "The bank is bankrupt. There are insufficient funds in the system to fulfill your withdrawal.")
            return redirect('transaction_report')  
        print(total_bank_balance)

        self.request.user.account.balance -= form.cleaned_data.get('amount')
        
        self.request.user.account.save(update_fields=['balance'])

        
        send_mail(self.request.user, self.request.user.email, amount, 'Withdraw Money', 'transactions/withdraw_mail.html')

        return super().form_valid(form)

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account,transaction_type=3,loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )
        send_mail(self.request.user, self.request.user.email, amount, 'Loan Request Message', 'transactions/loan_mail.html')

        return super().form_valid(form)
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0 
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct() # unique queryset hote hobe
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })

        return context
    
        
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
                
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(self.request, f'Loan amount is greater than available balance')
            return redirect('loan_list')
            
        

        return redirect('loan_list')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans' # loan list ta ei loans context er moddhe thakbe
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=3)
        print(queryset)
        return queryset
    
    
class TransferMoneyView(TransactionCreateMixin):
    form_class = TransferMoneyForm
    title = 'Transfer Money'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'sender_account': self.request.user.account})
        return kwargs

    def form_valid(self, form):
        sender_account = self.request.user.account
        receiver_account = form.receiver_account 
        amount = form.cleaned_data['amount']
        sender_account.balance -= amount
        sender_account.save()
        receiver_account.balance += amount
        receiver_account.save()
        
        Transaction.objects.create(
            account=sender_account,
            amount=-amount,
            transaction_type=TRANSFER,  
            balance_after_transaction=sender_account.balance
        )
        send_transfer_mail(self.request.user, receiver_account, self.request.user.email, amount, 'Transfer Money', 'transactions/send_money.html')
        
        Transaction.objects.create(
            account=receiver_account,
            amount=amount,
            transaction_type=TRANSFER, 
            balance_after_transaction=receiver_account.balance
        )
        send_transfer_mail(receiver_account, self.request.user.account, receiver_account.user.email, amount, 'Transfer Money', 'transactions/receive_money.html')

        messages.success(self.request, f'Transferred {"{:,.2f}".format(float(amount))}$ successfully to {receiver_account.account_no}')
        return super().form_valid(form)

