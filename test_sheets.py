import gspread


def get_values(worksheet):
    return worksheet.get_values()


def set_values(worksheet, values):
    return worksheet.update("A1", values)


def main():
    gc = gspread.service_account(filename="credentials.json")
    worksheet = gc.open("CI Is My DJ").sheet1

    values = get_values(worksheet)
    print(values)
    values[0][0] += "2"
    values[0][1] += "2"
    set_values(worksheet, values)
    values = get_values(worksheet)
    print(values)


if __name__ == "__main__":
    main()
