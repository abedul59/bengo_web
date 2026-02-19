from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StockData
import json
from datetime import datetime

# 首頁：上傳 + 查詢
def dashboard(request):
    # 處理 JSON 上傳
    if request.method == 'POST' and request.FILES.get('json_file'):
        try:
            f = request.FILES['json_file']
            data = json.load(f)
            
            stock_id = data.get('stock_id')
            stock_name = data.get('stock_name')
            history = data.get('history', [])

            for row in history:
                # 日期格式轉換 20260218 -> 2026-02-18
                d_str = str(row['date'])
                date_obj = datetime.strptime(d_str, "%Y%m%d").date()
                
                # 存入資料庫 (update_or_create: 如果有就更新，沒有就新增)
                StockData.objects.update_or_create(
                    stock_id=stock_id,
                    date=date_obj,
                    defaults={
                        'stock_name': stock_name,
                        'price': float(str(row['price']).replace(',', '')),
                        'total_shares': int(str(row['total_shares']).replace(',', '')),
                        'total_people': int(str(row['total_people']).replace(',', '')),
                        'bengo_threshold': row['threshold_str'],
                        'major_people': int(str(row['major_ppl']).replace(',', '')),
                        'major_pct': float(str(row['major_pct']).replace('%', '')),
                        'note': row.get('note', '')
                    }
                )
            messages.success(request, f"成功匯入 {stock_name} 的數據！")
            return redirect(f'/?stock={stock_id}') # 匯入後直接跳轉查詢
            
        except Exception as e:
            messages.error(request, f"匯入錯誤: {e}")

    # 查詢邏輯
    query_stock = request.GET.get('stock', '')
    chart_data = {}
    table_data = []
    
    if query_stock:
        # 抓取該股票的所有歷史資料，依日期排序 (給圖表用)
        qs = StockData.objects.filter(stock_id=query_stock).order_by('date')
        if qs.exists():
            chart_data = {
                'dates': [d.date.strftime('%Y/%m/%d') for d in qs],
                'prices': [d.price for d in qs],
                'major_pcts': [d.major_pct for d in qs]
            }
            # 表格資料用倒序 (最新的在上面)
            table_data = qs.order_by('-date')

    return render(request, 'dashboard.html', {
        'chart_data': json.dumps(chart_data),
        'table_data': table_data,
        'query_stock': query_stock
    })

