import sys
sys.path.append(r"C:\Program Files\Lumerical\v202\api\python")
import lumapi

charge = lumapi.DEVICE(hide=False)  # 👈 show GUI
print("CHARGE launched")

input("Press Enter to close CHARGE...")
charge.close()