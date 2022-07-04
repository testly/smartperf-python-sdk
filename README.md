
### readme 
**start_up.py**文件执行区域里面。  
先输入app_key, app_secret  
sdk = SmartPerfSdk("zTOPdfzM", "317696f41febc60ac51fb553301a2508")  
插入手机，滑动到你要录制的app屏幕上方,比如飞书
sdk.start_app_record_video("飞书", "feishu.mp4")
录屏使用了scrcpy 被一起在初始化时load_path了
