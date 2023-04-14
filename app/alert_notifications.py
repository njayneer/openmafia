from flask import flash

SUCCESS = 'alert-success'
WARNING = 'alert-warning'
DANGER = 'alert-danger'


def account_created():
    flash('Konto założone poprawnie. Zaloguj się korzystając z podanych danych.', category=SUCCESS)


def user_already_exists():
    flash('Użytkownik o podanym loginie już istnieje!', category=DANGER)


def email_already_taken():
    flash('Email już istnieje w systemie! Wybierz inny lub przejdź do strony logowania.', category=DANGER)


def login_incorrect():
    flash('Login lub hasło nieprawidłowe. Spróbuj ponownie.', category=DANGER)


def login_correct(user_name):
    flash(f'Witaj, {user_name}!', category=SUCCESS)


def player_name_set(player_name):
    flash(f'Nazwa gracza zmieniona na {player_name}', category=SUCCESS)


def player_name_not_set(player_name):
    flash(f'Nazwa gracza nie została zmieniona w wyniku błędu.', category=DANGER)
