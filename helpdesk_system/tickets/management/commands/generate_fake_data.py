import random
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from helpdesk_system.tickets.models import Comment
from helpdesk_system.tickets.models import Ticket
from helpdesk_system.users.models import User


class Command(BaseCommand):
    help = "Generate fake data for testing performance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tickets",
            type=int,
            default=10000,
            help="Number of tickets to create (default: 10000)",
        )
        parser.add_argument(
            "--comments-per-ticket",
            type=int,
            default=5,
            help="Average comments per ticket (default: 5)",
        )
        parser.add_argument(
            "--customers",
            type=int,
            default=50,
            help="Number of customer users to create (default: 50)",
        )
        parser.add_argument(
            "--agents",
            type=int,
            default=10,
            help="Number of agent users to create (default: 10)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for bulk operations (default: 1000)",
        )

    def handle(self, *args, **options):
        self.fake = Faker()
        self.batch_size = options["batch_size"]

        start_time = time.time()

        self.stdout.write(self.style.NOTICE("Starting fake data generation..."))

        # Generate users
        customers = self._create_users(
            count=options["customers"],
            role=User.Role.CUSTOMER,
            prefix="customer",
        )
        agents = self._create_users(
            count=options["agents"],
            role=User.Role.AGENT,
            prefix="agent",
        )

        all_users = customers + agents

        # Generate tickets
        tickets = self._create_tickets(
            count=options["tickets"],
            customers=customers,
            agents=agents,
        )

        # Generate comments
        self._create_comments(
            tickets=tickets,
            users=all_users,
            avg_per_ticket=options["comments_per_ticket"],
        )

        elapsed = time.time() - start_time

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Data generation completed in {elapsed:.2f} seconds!\n"
                f"   - {len(customers)} customers\n"
                f"   - {len(agents)} agents\n"
                f"   - {len(tickets)} tickets\n"
                f"   - ~{len(tickets) * options['comments_per_ticket']} comments",
            ),
        )

    @transaction.atomic
    def _create_users(self, count: int, role: str, prefix: str) -> list[User]:
        """Create users in bulk."""
        self.stdout.write(f"Creating {count} {role} users...")

        # Check existing users with this prefix
        existing = User.objects.filter(username__startswith=f"{prefix}_").count()

        users = []
        for i in range(count):
            user = User(
                username=f"{prefix}_{existing + i + 1}",
                email=f"{prefix}_{existing + i + 1}@test.com",
                role=role,
                name=self.fake.name(),
            )
            user.set_password("testpass123")
            users.append(user)

        User.objects.bulk_create(users, batch_size=self.batch_size)

        # Retrieve created users with IDs
        usernames = [u.username for u in users]
        return list(User.objects.filter(username__in=usernames))

    @transaction.atomic
    def _create_tickets(
        self,
        count: int,
        customers: list[User],
        agents: list[User],
    ) -> list[Ticket]:
        """Create tickets in bulk."""
        self.stdout.write(f"Creating {count} tickets...")

        statuses = [s[0] for s in Ticket.Status.choices]
        priorities = [p[0] for p in Ticket.Priority.choices]

        tickets = []
        for i in range(count):
            if i > 0 and i % self.batch_size == 0:
                self.stdout.write(f"  Progress: {i}/{count} tickets...")

            assigned_to = None
            status = random.choice(statuses)  # noqa: S311

            # Assign agent if not open
            if status != Ticket.Status.OPEN:
                assigned_to = random.choice(agents)  # noqa: S311

            tickets.append(
                Ticket(
                    title=self.fake.sentence(nb_words=6),
                    description=self.fake.paragraph(nb_sentences=3),
                    status=status,
                    priority=random.choice(priorities),  # noqa: S311
                    created_by=random.choice(customers),  # noqa: S311
                    assigned_to=assigned_to,
                ),
            )

        Ticket.objects.bulk_create(tickets, batch_size=self.batch_size)

        # Retrieve created tickets with IDs
        return list(
            Ticket.objects.order_by("-id")[:count].select_related(
                "created_by",
                "assigned_to",
            ),
        )

    @transaction.atomic
    def _create_comments(
        self,
        tickets: list[Ticket],
        users: list[User],
        avg_per_ticket: int,
    ) -> None:
        """Create comments in bulk."""
        total_comments = len(tickets) * avg_per_ticket
        self.stdout.write(f"Creating ~{total_comments} comments...")

        comments = []
        for i, ticket in enumerate(tickets):
            if i > 0 and i % self.batch_size == 0:
                self.stdout.write(
                    f"  Progress: {i}/{len(tickets)} tickets processed...",
                )

            # Random number of comments (0 to 2x average)
            num_comments = random.randint(0, avg_per_ticket * 2)  # noqa: S311

            comments.extend(
                Comment(
                    ticket=ticket,
                    author=random.choice(users),  # noqa: S311
                    content=self.fake.paragraph(nb_sentences=2),
                )
                for _ in range(num_comments)
            )

            # Bulk insert when batch is full
            if len(comments) >= self.batch_size:
                Comment.objects.bulk_create(comments, batch_size=self.batch_size)
                comments = []

        # Insert remaining comments
        if comments:
            Comment.objects.bulk_create(comments, batch_size=self.batch_size)
