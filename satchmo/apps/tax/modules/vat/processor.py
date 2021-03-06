from decimal import Decimal
from livesettings import config_value
from tax.models.processor import BaseProcessor

class Processor(BaseProcessor):
    """Simple VAT (Value Added Tax) for one country in Europe.
    Implemented 2 taxrates (normal and reduced) editable by settings

    One taxclass should be named 'ReducedVAT'. An arbitrary name is for a normal VAT tax.
    """
    
    method="vat"
    
    def by_orderitem(self, orderitem):
        if orderitem.product.taxable:
            price = orderitem.sub_total
            return self.by_price(orderitem.product.taxClass, price)
        else:
            return Decimal("0.00")
        
    def by_price(self, taxclass, price):
        if getattr(taxclass, 'title', None) != 'ReducedVAT':
            percent = config_value('TAX','PERCENT')
        else:
            percent = config_value('TAX','REDUCEDVAT')
        return price * (percent / 100)
        
    def by_product(self, product, quantity=Decimal('1')):
        price = product.get_qty_price(quantity)
        taxclass = product.taxClass
        return self.by_price(taxclass, price)
        
    def get_percent(self, taxclass='Default', *args, **kwargs):
        if getattr(taxclass, 'title', None) != 'ReducedVAT':
            return Decimal(config_value('TAX','PERCENT'))
        else:
            return Decimal(config_value('TAX','REDUCEDVAT'))
    
    def get_rate(self, *args, **kwargs):
        return self.get_percent(*args, **kwargs)/100
        
    def shipping(self, subtotal=None):
        if subtotal is None and self.order:
            subtotal = self.order.shipping_sub_total

        if subtotal:
            subtotal = self.order.shipping_sub_total
            if config_value('TAX','TAX_SHIPPING'):
                percent = config_value('TAX','PERCENT')
                t = subtotal * (percent/100)
            else:
                t = Decimal("0.00")
        else:
            t = Decimal("0.00")
                
        return t
            
    def process(self, order=None):
        """
        Calculate the tax and return it
        """
        if order:
            self.order = order
        else:
            order = self.order

        percent = config_value('TAX','PERCENT')    

        sub_total = Decimal("0.00")
        for item in order.orderitem_set.filter(product__taxable=True):
            sub_total += item.sub_total
        
        itemtax = sub_total * (percent/100)
        taxrates = {'%i%%' % percent :  itemtax}
        
        if config_value('TAX','TAX_SHIPPING'):
            shipping = order.shipping_sub_total
            sub_total += shipping
            ship_tax = shipping * (percent/100)
            taxrates['Shipping'] = ship_tax
        
        tax = sub_total * (percent/100)
        return tax, taxrates
