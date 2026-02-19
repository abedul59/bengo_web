from django.db import models

class StockData(models.Model):
    stock_id = models.CharField(max_length=10, verbose_name="股票代號")
    stock_name = models.CharField(max_length=50, verbose_name="股票名稱")
    date = models.DateField(verbose_name="資料日期") 
    
    price = models.FloatField(verbose_name="收盤價")
    total_shares = models.BigIntegerField(verbose_name="集保總張數")
    total_people = models.IntegerField(verbose_name="總股東人數")
    
    bengo_threshold = models.CharField(max_length=20, verbose_name="Bengo門檻")
    major_people = models.IntegerField(verbose_name="大戶人數")
    major_pct = models.FloatField(verbose_name="大戶比例")
    
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('stock_id', 'date') # 避免重複匯入同一天
        ordering = ['-date'] # 預設顯示最新的

    def __str__(self):
        return f"{self.stock_name} ({self.date})"
# Create your models here.
