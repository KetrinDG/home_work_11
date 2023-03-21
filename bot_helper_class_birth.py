import click
from collections import UserDict, defaultdict
from datetime import datetime, timedelta
import re
from typing import List
import pickle


class Field:
    def __init__(self, value):
        # если у нас наследование и в дочерних классах предвидится минимум переопределений используем _ одинарное подчеркивание (протектед)
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __repr__(self):
        return f"{self.value}"


class Name(Field):
    @Field.value.setter
    def value(self, name):
        if re.match(r"[a-zA-Z]+", name):
            self._value = name
        else:
            raise ValueError


class Phone(Field):
    @Field.value.setter
    def value(self, phone):
        if re.match(r"^\d{10,12}\d?", phone) or re.match(r"^\+\d{12}\d?", phone):
            self._value = phone
        else:
            raise ValueError('Phone must be only number or beging "+3...')


class Birthday(Field):
    @Field.value.setter
    def value(self, value):
        if value:
            try:
                birthday = datetime.strptime(value, "%Y/%m/%d").date()
                self._value = birthday
            except TypeError or ValueError:
                raise ValueError("Birthday must be year/month/date")
        else:
            self._value = ""


class Record:
    def __init__(self, name: Name, phone: Phone = None, birthday: Birthday = None):
        self.name = name
        self.phones = []
        if phone:
            self.phones.append(phone)
        self.birthday = birthday

    def __repr__(self):
        if self.birthday:
            return f"{self.name.value}: {[p.value for p in self.phones]}, Birthday: {self.birthday}"
        return f"{self.name.value}: {[p.value for p in self.phones]}"

    def add_phone(self, phone) -> None:
        self.phones.append(phone)

    def change_phone(self, phone, new_phone) -> None:
        for ph in self.phones:
            if ph.value == phone.value:
                self.phones.remove(ph)
                self.phones.append(new_phone)

    def del_phone(self, phone) -> None:
        self.phones.remove(phone)

    def __str__(self) -> str:
        return f"Contact {self.name}: Phones {self.phones}"

    def days_to_birthday(self):
        delta1 = datetime(
            datetime.now().year, self.birthday._value.month, self.birthday._value.day
        )
        delta2 = datetime(
            datetime.now().year + 1,
            self.birthday._value.month,
            self.birthday._value.day,
        )
        result = ((delta1 if delta1 > datetime.now() else delta2) - datetime.now()).days
        return f"Birthday is in {result} days."


class AddressBook(UserDict):
    def __repr__(self):
        return f"{self.data}"

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def iterator(self, num: int = 2):
        data = self.data
        items = list(data.items())
        counter = 0
        result = ""
        for i in items:
            result += f"{i}"
            counter += 1
            if counter >= num:
                yield result
                result = ""
                counter = 0
        yield result

    def show_all(self) -> str:
        return "\n".join([str(v) for v in self.items()])
        # отсутствует файл

    @classmethod
    def read_file(self):
        try:
            with open("contacts.bin", "rb") as file:
                return pickle.load(file)
        except FileNotFoundError:
            return AddressBook()

    def write_file(self):
        with open("contacts.bin", "wb") as file:
            pickle.dump(self, file)


# ошибка ввода
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return """If you write command 'add' please write 'add name number birthday(if you want)'\nIf you write command 'change' please write 'change name number'\nIf you write command 'phone' please write 'phone name'"""
        except KeyError:
            return "..."

    return wrapper


@input_error
def help_command():
    help_list = [
        "help - output command, that help find command",
        'hello - output command "How can I help you?"',
        'add - add contact, use "add" "name" "number" "birthday"',
        'change - change your contact, use "change" "name" "number"',
        'phone - use "phone" "name" that see number this contact',
        "show all - show all your contacts",
        "birthday name - show birthday",
    ]
    return "\n".join(help_list)


@input_error
def bye_command(*args):
    return "Good bye, see you soon"


@input_error
def hello_command(*args):
    return "How can I help You?\nIf you want to know what I can do write Help "


# создание контакта
@input_error
def add_phone(*args):
    name = Name(args[0])
    phone = Phone(args[1])
    contacts = AddressBook.read_file()
    try:
        birthday = Birthday(args[2])
    except IndexError:
        birthday = None
    if contacts.get(Name(args[0])):
        return "This contact already exist"
    else:
        rec = Record(name, phone, birthday)
        contacts.add_record(rec)
    contacts.write_file()
    return f'Contact "{name}" add successfully'


# изменение контакта
@input_error
def change_phone(*args):
    name = Name(args[0])
    phone = Phone(args[1])
    new_phone = Phone(args[2])
    contacts = AddressBook.read_file()
    reck: Record = contacts.get(name.value)
    if reck:
        reck.change_phone(phone, new_phone)
    else:
        return f'No contact "{name}"'
    AddressBook.write_file(contacts)
    return f"Contact '{name}' change successfully"


@input_error
def del_number(*args):
    name, phone = Name(args[0]), Phone(args[1])
    contacts = AddressBook.read_file()
    contacts[name.value].del_phone(phone.value)
    return f"Contact {name.value} has deleted successfully."


@input_error
def add_phone_command(*args):
    name = Name(args[0])
    contacts = AddressBook.read_file()
    if contacts.get(name):
        return "\t{:>20} : {:<12} ".format(name, contacts.get(name))
    else:
        return f'No contact "{name}"'


def birthday_contact(*args, **kwargs):
    name = Name(args[0])
    contacts_dict = AddressBook.read_file()
    contacts = contacts_dict.get(name)
    if isinstance(contacts, Record):
        if contacts.birthday._value is None:
            return "No birthday data available"
        else:
            result_bd = contacts.days_to_birthday()
            return f"{name.capitalize()}'s birthday is {contacts_dict[name].birthday}. {result_bd}"
    return "No personal record available"


# отобразить все


def show_all(*args, **kwargs):
    contacts = AddressBook.read_file()
    try:
        page = int(args[1])
    except IndexError:
        return contacts.show_all()

    result = ""
    for i in contacts.iterator(page):
        result += f"{i}\n"
    return result


# работа по командам


commands = {
    hello_command: ["hello", "hi"],
    add_phone: ["add", "new", "+"],
    add_phone_command: ["phone", "number"],
    show_all: ["show all", "show"],
    change_phone: ["change"],
    bye_command: ["good bye", "bye", ".", "close", "exit"],
    help_command: ["help"],
    del_number: ["del", "delete", "-"],
    birthday_contact: ["birthday", "bdate", "bd"],
}


def command_parser(user_input):
    data = []
    command = ""
    for k, v in commands.items():
        if any([user_input.lower().startswith(i) for i in v]):
            command = k
            data = [word for word in user_input.split() if word not in v]
            return command, data
    return None, None


def start_hello():
    return f"Hello, I'm a bot assistent.\nTo get started, write Hello"


@click.command()
def main():
    # начало программы
    while True:
        user_input = input(">>> ")
        command, data = command_parser(user_input)
        if command:
            print(command(*data))
            if command == bye_command:
                break
        else:
            print("Sorry, unknown command. Try again.")


if __name__ == "__main__":
    print(start_hello())
    main()
