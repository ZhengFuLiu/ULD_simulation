from py3dbp import Packer, Bin, Item, Painter
import streamlit as st

def auto_pack_items(items):
    """
    自動裝箱函數
    :param items: 用戶自行輸入尺寸表，包含長寬高與重量
    :return: 裝箱後結果
    """
    # 箱子尺寸與承重
    bin_length, bin_width, bin_height, bin_weight_limit = 10, 10, 10, 50
    # 初始化未裝箱的貨品
    unfit_items = items[:]
    bin_count = 0
    # 若有未裝箱，則新增一個箱子
    while unfit_items:
        # 建立Packer
        packer = Packer()
        # 新增箱子
        bin_count += 1
        for count in range(1, bin_count+1):
            new_bin = Bin(f'貨櫃-{count}', (bin_length, bin_width, bin_height), bin_weight_limit, 0, 0)
            packer.addBin(new_bin)
        # 嘗試裝箱
        for item_name, item_length, item_width, item_height, item_weight in items:
            packer.addItem(Item(partno=item_name, name=item_name, typeof='cube', WHD=(item_length, item_width, item_height), weight=item_weight,
                                level=1, loadbear=100, updown=True, color='olive'))
        # 執行裝箱演算法
        packer.pack(
            bigger_first=True,
            distribute_items=True,
            fix_point=True,
            check_stable=True,
            support_surface_ratio=0.75,
            number_of_decimals=0
        )
        # put order
        packer.putOrder()
        # 更新未裝箱的物品
        unfit_items = [(item.name, item.width, item.height, item.depth, item.weight) for item in packer.unfit_items]
    #輸出結果
    for b in packer.bins:
        volume = b.width * b.height * b.depth
        volume_t = 0
        # 輸出圖例
        painter = Painter(b)
        fig = painter.plotBoxAndItems(
            title=b.partno,
            alpha=0.2,
            write_num=True,
            fontsize=10
        )
        st.pyplot(fig)
        # 顯示裝入箱子中的貨品
        st.caption(b.string())
        for item in b.items:
            st.text(f"貨物：{item.partno}  位置：{item.position}  旋轉：{item.rotation_type}")
            volume_t += float(item.width) * float(item.height) * float(item.depth)
        st.text('空間使用率 : {}%'.format(round(volume_t / float(volume) * 100 ,2)))

def page_config():
    #網頁呈現資訊
    st.set_page_config(
        page_title="Axon",
        page_icon="🚜",
        initial_sidebar_state="auto",
        menu_items={
            'About': "築打模擬系統"
        } 
    )

def main_page():
    # 新增函數
    def add_item(name, length, width, height, weight):
        """ Add an item to the list. """
        return name, length, width, height, weight
    # 一鍵清空
    def display_items(item_list):
        """ Display items in the list in a grid layout. """
        items = []
        if not item_list:
            st.success("No items to display.", icon="✅")
            return items
        else:
            for i in range(len(item_list) // 6 + (1 if len(item_list) % 6 != 0 else 0)):
                # Creating 10 columns for each row
                cols = st.columns(6)
                # Slicing the list to get up to 10 items for the current row
                for idx, item in enumerate(item_list[i*6:(i+1)*6]):
                    a = cols[idx].checkbox(item[0], value=True)
                    items.append(a)
            return items
    # 主頁設定
    st.title('📦築打模擬系統')
    st.subheader('🎁自行輸入貨物資訊')
    st.subheader('🎁一鍵模擬自動裝箱與輸出展示圖')
    st.subheader('🎁考量貨物穩定度與優先權，並最大化空間使用率')
    st.markdown('#')
    # 新增貨物列表狀態
    if 'items' not in st.session_state:
        st.session_state['items'] = []
    # 初始化輸入貨物
    labels = ['貨物名稱', '長度(m)', '寬度(m)', '高度(m)', '重量(kg)']
    for label in labels:
        if label not in st.session_state:
            st.session_state[label] = ''
    # 區塊顯示
    with st.container():
        col_layout = st.columns(5)
        # 輸入尺寸與重量
        item_details = [col.text_input(label, st.session_state[label]) for col, label in zip(col_layout, labels)]
        # 顯示輸入資訊
        item_info = '  '.join([f'{label}：{detail}' for label, detail in zip(labels, item_details)])
        st.text(item_info)
        # 新增鍵與刪除鍵
        butt1, butt2 = st.columns(9)[7:]
        add = butt1.button("新增", type="primary")
        delete = butt2.button("清除")
    # 新增貨物
    if add:
        st.session_state['items'].append(add_item(*item_details))
        for label in labels:
            st.session_state[label] = ''
    # 刪除列表
    if delete:
        st.session_state['items'].clear()
    # 顯示目前貨物
    items = display_items(st.session_state['items'])
    
    # 使用自動裝箱函數
    if len(st.session_state['items']) > 0:
        filtered_list = [item for item, include in zip(st.session_state['items'], items) if include]
        try:
            auto_pack_items(filtered_list)
        except:
            st.error("輸入物品尺寸超出限制範圍，貨櫃尺寸:(10*10*10,限重50)", icon="🚨")

if __name__ == "__main__":
    # 網頁資訊
    page_config()
    # 主頁
    main_page()