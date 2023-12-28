from py3dbp import Packer, Bin, Item, Painter
import streamlit as st

def auto_pack_items(items, bin_limits):
    """
    Automatically pack items into bins.
    
    :param items: List of user-inputted items, each with name, length, width, height, and weight.
    :param bin_limits: Tuple containing the bin's dimensions (length, width, height) and weight limit.
    :return: None. The function directly visualizes and displays the packing results in the Streamlit app.
    """
    # Unpack bin dimensions and weight limit
    bin_length, bin_width, bin_height, bin_weight_limit = bin_limits

    # Copy items to track those that are not yet packed
    unfit_items = items[:]
    bin_count = 0

    # Continue adding bins until all items are packed
    while unfit_items:
        packer = Packer()

        # Increment bin count and add new bins
        bin_count += 1
        for count in range(1, bin_count+1):
            new_bin = Bin(f'貨櫃-{count}', (bin_length, bin_width, bin_height), bin_weight_limit, 0, 0)
            packer.addBin(new_bin)

        # Define color mapping for item levels
        color_map = {'優先': 'brown', '普通': 'yellow', '非優先': 'olive'}

        # Add items to the packer with conditional attributes
        for item in items:
            item_name, item_length, item_width, item_height, item_weight, item_loadbear, item_updown, item_level = item
            packer.addItem(Item(partno=item_name, name=item_name, typeof='cube', WHD=(item_length, item_width, item_height), weight=item_weight,
                                level={'優先': 1, '普通': 2, '非優先': 3}[item_level], loadbear=((item_loadbear == "是") and 300 or 1), updown=((item_updown == "是") and True or False), color=color_map.get(item_level)))
        # Execute packing algorithm with specified parameters
        packer.pack(
            bigger_first=True,
            distribute_items=True,
            fix_point=True,
            check_stable=True,
            support_surface_ratio=0.75,
            number_of_decimals=0
        )

        # Update the list of items that are still unfit
        unfit_items = [(item.name, item.width, item.height, item.depth, item.weight) for item in packer.unfit_items]

        # Arrange items in the order of packing
        packer.putOrder()

    if len(items) > 0:
        # Visualize and display results for each bin
        for b in packer.bins:
            # Calculate the total volume of the bin
            volume = b.width * b.height * b.depth
            volume_t = 0
            
            # Create a visual representation of the bin and its contents
            painter = Painter(b)
            fig = painter.plotBoxAndItems(
                title=b.partno,
                alpha=0.2,
                write_num=True,
                fontsize=10
            )
            st.pyplot(fig)

            # Display details about the packed items in the bin
            st.caption(b.string())
            for item in b.items:
                st.text(f"貨物：{item.partno}  位置：{item.position}  旋轉：{item.rotation_type}")
                volume_t += float(item.width) * float(item.height) * float(item.depth)
            
            # Calculate and display the space utilization rate
            st.text('空間使用率 : {}%'.format(round(volume_t / float(volume) * 100 ,2)))

def add_item(name, length, width, height, weight, loadbear, updown, level):
    """ Add an item to the list. """
    return name, length, width, height, weight, loadbear, updown, level

def display_items(item_list):
    """ Display input items and allow selection for packing. """
    if not item_list:
        st.success("No items to display.", icon="✅")
        return []

    item_strings = [f'{item[0]}-{item[1]}*{item[2]}*{item[3]}, 重量:{item[4]}' for item in item_list]
    # Create a multiselect widget for item selection
    selected_items = st.multiselect("選擇要裝箱的貨物", item_strings, item_strings)
    return selected_items 

def is_valid_item(item, bin_limits):
    """
    Check if the item is valid based on bin limits.
    :param item: Tuple containing the item's dimensions and weight.
    :param bin_limits: Tuple containing the bin's dimensions and weight limit.
    :return: Boolean indicating whether the item is valid.
    """
    _, item_length, item_width, item_height, item_weight = item[:5]
    bin_length, bin_width, bin_height, bin_weight_limit = bin_limits
    return all([
        float(item_length) <= float(bin_length),
        float(item_width) <= float(bin_width),
        float(item_height) <= float(bin_height),
        float(item_weight) <= float(bin_weight_limit)
    ])

def page_config():
    """
    Configure the Streamlit page settings.
    """

    # Set up the configuration of the Streamlit page
    st.set_page_config(
        page_title="Axon", # Title of the page, displayed in the browser tab
        page_icon="🚜",    # Icon (emoji or image) displayed in the browser tab
        initial_sidebar_state="auto",  # Default state of the sidebar ('auto', 'expanded', 'collapsed')
        menu_items={
            'About': "築打模擬系統"  # Custom text for the 'About' menu item
        } 
    )

def main_page():
    # Set up the main page layout and titles
    st.title('📦築打模擬系統')
    st.subheader('🎁自行輸入貨物資訊與盤型限制')
    st.subheader('🎁一鍵模擬自動裝箱與輸出展示圖')
    st.subheader('🎁考量貨物穩定度與優先權，並最大化空間使用率')
    st.markdown('#')  # Adds a visual separator
    
    # Initialize or retrieve the list of items from the session state
    if 'items' not in st.session_state:
        st.session_state['items'] = []

    # Define bin dimensions and weight limit
    bin_layout = st.columns(4)
    bin_labels = ['盤型限長(m)', '盤型限寬(m)', '盤型限高(m)', '盤型限重(g)']

    # Initialize input labels and values in the session state
    labels = ['貨物名稱', '長度(m)', '寬度(m)', '高度(m)', '重量(g)', '可壓', '可倒放', '優先權']
    for label in labels:
        if label not in st.session_state:
            st.session_state[label] = ''
    for label in bin_labels:
        if label not in st.session_state:
            st.session_state[label] = ''
    
    bin_limits = [col.number_input(label) for col, label in zip(bin_layout, bin_labels)]
    button = st.columns(6)[-1]
    act = button.button("生成盤型")

    # Input section for item dimensions and weight
    with st.container():
        col_layout = st.columns(5)
        item_details = [col_layout[0].text_input(labels[0], st.session_state[labels[0]])]
        item_details = [*item_details, *[col.number_input(label) for col, label in zip(col_layout[1:5], labels[1:5])]]
        
        twice_col = st.columns(3)
        item_details.append(twice_col[0].radio(labels[5], ["是", "否"], horizontal=True))
        item_details.append(twice_col[1].radio(labels[6], ["是", "否"], horizontal=True))
        item_details.append(twice_col[2].select_slider(labels[7], options=['非優先', '普通', '優先'], value='普通'))

        # Buttons for adding new items and clearing the list
        butt1, butt2 = st.columns(9)[7:]
        add = butt1.button("新增", type="primary")
        delete = butt2.button("清除")
        st.write("---")

    # Handling the addition of new items
    if add:
        # Validate and add items to the list
        try:
            _ = [float(i) for i in item_details[1:5]]  # Check if dimensions and weight are numeric
            new_item = add_item(*item_details)

            # Validate the new item's dimensions and check for duplicate names
            if is_valid_item(new_item, bin_limits):
                # Check for duplicate names
                if any(item[0] == new_item[0] for item in st.session_state['items']):
                    st.error("相同名稱已存在，請更改名稱再重新新增", icon="🚨")
                else:
                    st.session_state['items'].append(new_item)
                    # Clear input fields after successful addition
                    for label in labels:
                        st.session_state[label] = ''
            else:
                st.error(f"新增的物品尺寸或重量超出貨櫃限制，貨櫃尺寸:({bin_limits[0]}x{bin_limits[1]}x{bin_limits[2]}, 限重：{bin_limits[3]})。", icon="🚨")
        except ValueError:
            st.error("請輸入數字。", icon="🚨")
    
    # Handling the clearing of the item list
    if delete:
        st.session_state['items'] = []

    # Display current items and allow selection for packing
    selected_items = [item_name.split("-")[0] for item_name in display_items(st.session_state['items'])]

    if act:
        packer = Packer()
        new_bin = Bin(f'盤型', (bin_limits[0], bin_limits[1], bin_limits[2]), bin_limits[3], 0, 0)
        packer.addBin(new_bin)
        
        for b in packer.bins:
            # Calculate the total volume of the bin
            volume = b.width * b.height * b.depth
            volume_t = 0
            
            # Create a visual representation of the bin and its contents
            painter = Painter(b)
            fig = painter.plotBoxAndItems(
                title=b.partno,
                alpha=0.2,
                write_num=True,
                fontsize=10
            )
            st.pyplot(fig)

    # Execute auto-packing function with selected items
    if len(st.session_state['items']) > 0:
        filtered_list = [item for item in st.session_state['items'] if item[0] in selected_items]
        auto_pack_items(filtered_list, bin_limits)
        

if __name__ == "__main__":
    # Configure the web page's appearance and settings
    page_config()

    # Display the main page content
    main_page()