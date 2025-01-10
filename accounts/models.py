from django.db import models
from django.contrib.auth.models import User



GENDER_TYPE = (
    ('Male', 'Male'),
    ('Female', 'Female'),
)

class UserBankAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    account_type = models.CharField(max_length=10, choices=[('Savings', 'Savings'), ('Current', 'Current')])
    account_no = models.CharField(max_length=10, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_TYPE)
    initial_deposit_date = models.DateField(auto_now_add=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return self.account_no
    
    
    
class UserAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='address')
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    postal_code = models.IntegerField()
    
    country = models.CharField(max_length=50)
    
    
    def __str__(self):
        return self.user.username