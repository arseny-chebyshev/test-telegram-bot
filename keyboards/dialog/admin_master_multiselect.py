import operator
from loader import db_session
from aiogram.types import CallbackQuery
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram_dialog import Window, Dialog, DialogManager
from aiogram_dialog.widgets.kbd import Multiselect, Button, Group
from aiogram_dialog.widgets.text import Format, Const
from sqlalchemy import select
from models.table_models import Service, Master, service_master_table
from .actions import cancel


class MasterMultiselect(StatesGroup):
    inserting_price = State()
    inserting_service = State()


async def get_services_all(**kwargs):
    async with db_session() as session:
        result = await session.execute(select(Master))
        masters = [res for res in result.scalars()]
        await session.commit()
    master_list = [(master, master.master_id) for master in masters]
    return {"masters": master_list}


async def add_masters_to_service(c: CallbackQuery, b: Button, d: DialogManager):
    masters = d.data['aiogd_context'].widget_data['m_masters']
    await d.data['state'].update_data({'masters': masters})
    dialog_data = await d.data['state'].get_data()
    service = Service(service_name=f"{dialog_data['service']}", price=f"{dialog_data['price']}")
    async with db_session() as session:
        session.add(service)
        await session.flush()
        for _ in dialog_data['masters']:
            await session.execute(service_master_table.insert().
                                  values(master=int(_), service=service.service_id))
        await session.commit()
    await c.message.delete()
    await c.message.answer(text=f"Masters added to service. Thank you!")
    await d.mark_closed()
    await d.data['state'].reset_state(with_data=True)


add_master_dialog = Dialog(Window(Const('Choose masters:'),
                                  Group(Multiselect(
                                             Format("✓ {item[0].master_name}"),
                                             Format("{item[0].master_name}"),
                                             id="m_masters", items='masters',
                                             item_id_getter=operator.itemgetter(1)),
                                        width=2),
                                  Button(Const("Submit"),
                                         id='submit',
                                         on_click=add_masters_to_service),
                                  Button(Const("Cancel"),
                                         id='cancel',
                                         on_click=cancel),
                           getter=get_services_all,
                           state=MasterMultiselect.inserting_service))