from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StockData
import json
from datetime import datetime, timedelta # [新增] 引入 timedelta
import traceback

def dashboard(request):
    # ... (上傳部分的程式碼保持不變) ...

    # --- 查詢邏輯 ---
    query_stock = request.GET.get('stock', '')
    chart_data = {}
    table_data = []
    stock_name_display = ""
    
    if query_stock:
        # 1. 取得該股票所有資料 (給表格用，依日期倒序)
        qs_all = StockData.objects.filter(stock_id=query_stock).order_by('-date')
        
        if qs_all.exists():
            stock_name_display = qs_all.first().stock_name
            table_data = qs_all # 表格顯示所有歷史資料
            
            # 2. [關鍵修改] 準備圖表資料 (只抓最近 180 天，依日期正序)
            six_months_ago = datetime.now().date() - timedelta(days=180)
            
            # 過濾出最近半年的資料，並轉回正序 (舊->新) 畫圖才對
            qs_chart = qs_all.filter(date__gte=six_months_ago).order_by('date')
            
            # 如果半年內沒資料(例如很久沒更新)，至少抓最後 30 筆，避免圖表全空
            if not qs_chart.exists():
                 qs_chart = qs_all.order_by('-date')[:30][::-1]

            chart_data = {
                'dates': [d.date.strftime('%Y/%m/%d') for d in qs_chart],
                'prices': [d.price for d in qs_chart],
                'major_pcts': [d.major_pct for d in qs_chart]
            }
        else:
            stock_name_display = query_stock

    return render(request, 'dashboard.html', {
        'chart_data': json.dumps(chart_data),
        'table_data': table_data,
        'query_stock': query_stock,
        'stock_name_display': stock_name_display
    })