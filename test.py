from django.db import transaction
from django.core.cache import cache
from base.managers import HasRelatedStore, ListCreateAPIView
from rest_framework.permissions import AllowAny

from common_config.api_code import HTTP_OK, UAT_URL
from utils.api_response import APIResponse
from products.models.product import Product, ProductAttribute
from products.views.image_manager import multikeysort


def product_price_and_images(product, attrs_selected):
    price = sum(ProductAttribute.objects.filter(id__in=attrs_selected).values_list('price', flat=True)) + product.price
    images = []
    for image_id in product.image_ids.all():
        if all([True if id in image_id.image_attributes.values_list('id', flat=True) else False for id in
                attrs_selected]):
            images.append(image_id.image.url)
    return price, images


class PreviewItem(ListCreateAPIView):
    queryset = ProductAttribute.objects.all()
    permission_classes = [AllowAny]

    def get_child_data(self, selected_attrs, result, tree_level):
        new_selected_attrs = []
        for attribute in selected_attrs:
            if tree_level % 2 != 0:
                for attr_id in attribute.child_ids.all().order_by('sequence'):
                    root_id = attr_id.get_root_attribute()
                    item = {'id': attr_id.id, 'name': attr_id.attribute, 'values': [], 'sequence': attr_id.sequence, 'level': tree_level, 'visible': 1}
                    result.setdefault(root_id.id, [])
                    result[root_id.id].append(item)

                    is_first_child = True
                    for child in attr_id.child_ids.all().order_by('sequence'):
                        image_url = ""
                        if child.thumbnail_id.all():
                            image_url = child.thumbnail_id.all()[0].image.url
                        item['values'].append({'id': child.id,
                                               'name': child.attribute,
                                               'selected': 1 if is_first_child else 0,
                                               'sequence': child.sequence,
                                               'image': image_url})
                        if is_first_child and child.child_ids.all():
                            new_selected_attrs.append(child)
                        is_first_child = False
            else:
                root_id = attribute.get_root_attribute()
                item = {'id': attribute.id, 'name': attribute.attribute, 'values': [], 'sequence': attribute.sequence, 'level': tree_level, 'visible': 1}
                result.setdefault(root_id.id, [])
                result[root_id.id].append(item)

                is_first_child = True
                for child in attribute.child_ids.all().order_by('sequence'):
                    image_url = ""
                    if child.thumbnail_id.all():
                        image_url = child.thumbnail_id.all()[0].image.url
                    item['values'].append({'id': child.id,
                                           'name': child.attribute,
                                           'selected': 1 if is_first_child else 0,
                                           'sequence': child.sequence,
                                           'image': image_url})
                    if is_first_child and child.child_ids.all():
                        new_selected_attrs.append(child)
                    is_first_child = False
        return new_selected_attrs, result

    def get_product_preview(self, product=None, attr_id=None):
        if attr_id:
            attr_id = self.get_object_or_404(ProductAttribute, id=attr_id)
            attribute_ids = attr_id.child_ids.all().order_by('sequence')
        else:
            attribute_ids = product.attribute_ids.filter(parent_id=None).order_by('sequence')
        product_attr_ids = [attr_id for attr_id in attribute_ids]
        selected_attrs = [attr_id for attr_id in product_attr_ids]

        result = {}
        if product_attr_ids:
            tree_level = product_attr_ids[0].level if attr_id else 0
            while selected_attrs:
                selected_attrs, result = self.get_child_data(selected_attrs, result, tree_level)
                if selected_attrs:
                    tree_level = selected_attrs[0].level
        return result

    def add_hidden_preview_data(self, product=None, keys=[], preview_data={}):
        result = []
        for attr_id in product.attribute_ids.all():
            if attr_id.id not in keys and attr_id.level % 2 == 0:
                root_id = attr_id.get_root_attribute()
                item = {
                    "id": attr_id.id,
                    "name": attr_id.attribute,
                    "level": attr_id.level,
                    "sequence": attr_id.sequence,
                    "visible": 0,
                    "root_id": root_id.id,
                }
                values = []
                for child in attr_id.child_ids.all().order_by('sequence'):
                    values.append({
                        "id": child.id,
                        "name": child.attribute,
                        "image": child.thumbnail_id.all()[0].image.url if child.thumbnail_id.all() else '',
                        'selected': 0,
                        'sequence': child.sequence,
                    })
                item['values'] = values
                result.append(item)
        sorted_result = multikeysort(result, ['level', 'sequence'])
        for data in sorted_result:
            preview_data[data['root_id']].append(data)
        return preview_data

    def get(self, request, args, *kwargs):
        product = self.get_object_or_404(Product, id=kwargs['pk'])
        cache_key = 'preview_product_' + str(kwargs['pk'])
        preview_data = cache.get(cache_key)
        if not preview_data:
            preview_data = self.get_product_preview(product=product)
            attrs_selected = []
            available_keys = []
            for list in preview_data.values():
                for data in list:
                    for item in data['values']:
                        if item['selected']:
                            attrs_selected.append(item['id'])
                    available_keys.append(data['id'])
            attrs_selected = [item['id'] for i in preview_data.values() for j in i for item in j['values'] if item['selected']]
            preview_data = self.add_hidden_preview_data(product, available_keys, preview_data)
            price, images = product_price_and_images(product, attrs_selected)
            result = {'product_name': product.name, 'price': price, 'images': images, 'preview_data': preview_data}
            cache.set(cache_key, result, None)
            return APIResponse(result, HTTP_OK)
        else:
            return APIResponse(preview_data, HTTP_OK)

    @transaction.atomic
    def post(self, request, args, *kwargs):
        product = self.get_object_or_404(Product, id=kwargs['pk'])

        def get_all_related_child(attribute_id, child_ids=[]):
            attribute = self.get_object_or_404(ProductAttribute, id=attribute_id)
            for child in attribute.child_ids.all():
                child_ids.append(child.id)
                get_all_related_child(child.id, child_ids)
            return child_ids

        last_selected = request.data['last_selected']
        current_selected = request.data['current_selected']

        child_ids = get_all_related_child(last_selected, [last_selected])
        total_last_selected = request.data['total_selected']
        common_attr_selected = list(set(total_last_selected) - set(child_ids)) + [current_selected]
        common_attr = product.attribute_ids.filter(id__in=common_attr_selected)

        old_attr_selected = [{'div_id': attr.parent_id.id, 'thumbnail_id': attr.id} for attr in common_attr]
        cache_key = 'preview_product_' + str(kwargs['pk']) + '_attribute_' + str(current_selected)
        new_data = cache.get(cache_key)
        if not new_data:
            new_data = self.get_product_preview(attr_id=current_selected)
            cache.set(cache_key, new_data, None)
        new_attr_selected = [{'div_id': data['id'], 'thumbnail_id': item['id']} for values in new_data.values() for data in values for item in data['values'] if item['selected'] or item['id'] in common_attr_selected]

        attrs_selected = old_attr_selected + new_attr_selected
        price, images = product_price_and_images(product, [attr['thumbnail_id'] for attr in attrs_selected])
        result = {'product_name': product.name, 'price': price, 'images': images, 'preview_data': attrs_selected}
        return APIResponse(result, HTTP_OK)
