from pprint import pprint

from main import (
    book_job,
    get_availability
)


def test_availability():

    print("=" * 50)
    print("Testing availability")

    available = get_availability(
        "2026-06-30T14:00:00+00:00"
    )

    print("Available:", available)


def test_booking():

    print("=" * 50)
    print("Testing booking")

    job = {
        "customer_name": "John Smith",
        "phone_number": "555-1234",
        "address": "123 Main Street",
        "category": "General",
        "description": "Testing insert",
        "scheduled_start_time": "2026-06-30T14:00:00"
    }

    result = book_job(job)

    pprint(result)


if __name__ == "__main__":

    test_availability()

    test_booking()

    print("\nFinished.")