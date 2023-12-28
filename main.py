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
    (bin_length, bin_width, bin_height, bin_weight_limit) = bin_limits

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

        # Add items to the packer
        for item_name, item_length, item_width, item_height, item_weight, item_loadbear, item_updown, item_level in items:
            if item_level == "優先":
                packer.addItem(Item(partno=item_name, name=item_name, typeof='cube', WHD=(item_length, item_width, item_height), weight=item_weight,
                                    level=1, loadbear=((item_loadbear == "是") and 100 or 1), updown=((item_updown == "是") and True or False), color='brown'))
            elif item_level == "普通":
                packer.addItem(Item(partno=item_name, name=item_name, typeof='cube', WHD=(item_length, item_width, item_height), weight=item_weight,
                                    level=2, loadbear=((item_loadbear == "是") and 100 or 1), updown=((item_updown == "是") and True or False), color='yellow'))
            else:
                packer.addItem(Item(partno=item_name, name=item_name, typeof='cube', WHD=(item_length, item_width, item_height), weight=item_weight,
                                    level=3, loadbear=((item_loadbear == "是") and 100 or 1), updown=((item_updown == "是") and True or False), color='olive'))
        
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
    else:
        # Extract item names for the multiselect options
        item_names = [item[0] for item in item_list]

        # Create a multiselect widget for item selection
        selected_items = st.multiselect("選擇要裝箱的貨物", item_names, item_names)
        return selected_items 

def is_valid_item(item, bin_limits):
    """
    Check if the item is valid based on bin limits.
    :param item: Tuple containing the item's dimensions and weight.
    :param bin_limits: Tuple containing the bin's dimensions and weight limit.
    :return: Boolean indicating whether the item is valid.
    """
    _, item_length, item_width, item_height, item_weight, loadbear, updown, level = item
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
    st.subheader('🎁自行輸入貨物資訊')
    st.subheader('🎁一鍵模擬自動裝箱與輸出展示圖')
    st.subheader('🎁考量貨物穩定度與優先權，並最大化空間使用率')
    st.markdown('#')  # Adds a visual separator
    
    # Initialize or retrieve the list of items from the session state
    if 'items' not in st.session_state:
        st.session_state['items'] = []
    
    # Define bin dimensions and weight limit
    bin_limits = (10, 10, 10, 50)

    # Initialize input labels and values in the session state
    labels = ['貨物名稱', '長度(m)', '寬度(m)', '高度(m)', '重量(kg)', '可壓', '可倒放', '優先權']
    for label in labels:
        if label not in st.session_state:
            st.session_state[label] = ''
    
    # Input section for item dimensions and weight
    with st.container():
        col_layout = st.columns(8)
        item_details = [col.text_input(label, st.session_state[label]) for col, label in zip(col_layout[:5], labels[:5])]
        item_details.append(col_layout[5].radio(labels[5], ["是", "否"]))
        item_details.append(col_layout[6].radio(labels[6], ["是", "否"]))
        item_details.append(col_layout[7].select_slider(labels[7], options=['稍後', '普通', '優先'], value='普通'))
        item_info = '  '.join([f'{label}：{detail}' for label, detail in zip(labels, item_details)])
        st.text(item_info)

        # Buttons for adding new items and clearing the list
        butt1, butt2 = st.columns(9)[7:]
        add = butt1.button("新增", type="primary")
        delete = butt2.button("清除")

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
                st.error("新增的物品尺寸或重量超出貨櫃限制，貨櫃尺寸:(10x10x10,限重50)。", icon="🚨")
        except ValueError:
            st.error("請輸入數字。", icon="🚨")
    
    # Handling the clearing of the item list
    if delete:
        st.session_state['items'].clear()

    # Display current items and allow selection for packing
    selected_items = display_items(st.session_state['items'])

    # Execute auto-packing function with selected items
    if len(st.session_state['items']) > 0:
        filtered_list = [item for item, include in zip(st.session_state['items'], selected_items) if include]
        auto_pack_items(filtered_list, bin_limits)
        

if __name__ == "__main__":
    # Configure the web page's appearance and settings
    page_config()

    # Display the main page content
    main_page()