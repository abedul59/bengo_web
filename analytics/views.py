from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction  # [新增] 引入交易控制
from .models import StockData
import json
from datetime import datetime
import traceback

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

            # 清洗函式
            def clean_int(v):
                if v is None or v == "": return 0
                try:
                    s = str(v).replace(',', '').strip()
                    f = float(s)
                    return int(f)
                except: return 0

            def clean_float(v):
                if v is None or v == "": return 0.0
                try:
                    return float(str(v).replace(',', '').replace('%', '').strip())
                except: return 0.0

            count = 0
            
            # [關鍵修正] 開啟交易原子性 (Atomic Transaction)
            # 這會將整個迴圈的操作打包成一次資料庫提交，大幅提升速度並避免 Timeout
            with transaction.atomic():
                for row in history:
                    d_val = row.get('date')
                    d_str = str(d_val).split('.')[0]
                    
                    try:
                        date_obj = datetime.strptime(d_str, "%Y%m%d").date()
                    except ValueError:
                        continue
                    
                    StockData.objects.update_or_create(
                        stock_id=stock_id,
                        date=date_obj,
                        defaults={
                            'stock_name': stock_name,
                            'price': clean_float(row.get('price')),
                            'total_shares': clean_int(row.get('total_shares')),
                            'total_people': clean_int(row.get('total_people')),
                            'bengo_threshold': row.get('threshold_str', ''),
                            'major_people': clean_int(row.get('major_ppl')),
                            'major_pct': clean_float(row.get('major_pct')),
                            'note': row.get('note', '')
                        }
                    )
                    count += 1
                
            messages.success(request, f"成功匯入 {stock_name} ({stock_id}) 共 {count} 筆資料！")
            return redirect(f'/?stock={stock_id}')
            
        except Exception as e:
            print(traceback.format_exc()) # 在 Render Log 印出詳細錯誤
            messages.error(request, f"匯入錯誤: {e}")

    # 查詢邏輯 (保持不變)
    query_stock = request.GET.get('stock', '')
    chart_data = {}
    table_data = []
    stock_name_display = ""
    
    if query_stock:
        qs = StockData.objects.filter(stock_id=query_stock).order_by('date')
        if qs.exists():
            stock_name_display = qs.first().stock_name
            chart_data = {
                'dates': [d.date.strftime('%Y/%m/%d') for d in qs],
                'prices': [d.price for d in qs],
                'major_pcts': [d.major_pct for d in qs]
            }
            table_data = qs.order_by('-date')
        else:
            stock_name_display = query_stock

    return render(request, 'dashboard.html', {
        'chart_data': json.dumps(chart_data),
        'table_data': table_data,
        'query_stock': query_stock,
        'stock_name_display': stock_name_display
    })