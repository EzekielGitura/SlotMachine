import time

from game import SAVE_FILE, Player, SlotGame


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False


def write(message=""):
    if RICH_AVAILABLE:
        console.print(message)
    else:
        print(strip_rich_tags(str(message)))


def strip_rich_tags(text):
    return (
        text.replace("[bold]", "")
        .replace("[/bold]", "")
        .replace("[green]", "")
        .replace("[/green]", "")
        .replace("[red]", "")
        .replace("[/red]", "")
        .replace("[yellow]", "")
        .replace("[/yellow]", "")
        .replace("[cyan]", "")
        .replace("[/cyan]", "")
        .replace("[magenta]", "")
        .replace("[/magenta]", "")
    )


def ask(prompt):
    return input(strip_rich_tags(prompt))


def ask_positive_number(prompt):
    while True:
        value = ask(prompt)
        if value.isdigit() and int(value) > 0:
            return int(value)
        write("[red]Please enter a positive number.[/red]")


def ask_player():
    if SAVE_FILE.exists():
        answer = ask("Load saved game? [y/N] ").strip().lower()
        if answer == "y":
            player = Player.load(SAVE_FILE)
            write(f"[green]Loaded {player.name} with ${player.balance}.[/green]")
            return player

    name = ask("Player name: ").strip() or "Player"
    balance = ask_positive_number("Starting deposit: $")
    return Player(name=name, balance=balance)


def ask_paylines(game):
    while True:
        value = ask(
            f"Paylines to play (1-{game.slot_machine.max_paylines}): "
        ).strip()
        if value.isdigit():
            lines = int(value)
            if 1 <= lines <= game.slot_machine.max_paylines:
                return lines
        write("[red]Choose a valid number of paylines.[/red]")


def ask_bet(game):
    while True:
        value = ask(
            f"Bet per payline (${game.slot_machine.min_bet}-${game.slot_machine.max_bet}): $"
        ).strip()
        if value.isdigit():
            bet = int(value)
            if game.slot_machine.min_bet <= bet <= game.slot_machine.max_bet:
                return bet
        write("[red]Choose a valid bet.[/red]")


def show_header(player):
    title = (
        f"[bold]Supercharged Slot Machine[/bold]\n"
        f"{player.name} | Balance: [green]${player.balance}[/green] | "
        f"Free spins: [cyan]{player.free_spins}[/cyan]"
    )
    if RICH_AVAILABLE:
        console.print(Panel(title, border_style="magenta"))
    else:
        write("\nSupercharged Slot Machine")
        write(
            f"{player.name} | Balance: ${player.balance} | Free spins: {player.free_spins}"
        )


def show_menu(player):
    show_header(player)
    write("[Enter] Spin  |  p Paytable  |  s Stats  |  h History  |  v Save  |  l Load  |  q Quit")
    return ask("> ").strip().lower()


def show_reels(game, columns):
    labels = [
        [game.slot_machine.pay_table.label_for(symbol) for symbol in column]
        for column in columns
    ]

    if RICH_AVAILABLE:
        table = Table(show_header=False, box=None, pad_edge=False)
        for _ in labels:
            table.add_column(justify="center", width=8)

        for row in range(game.slot_machine.rows):
            table.add_row(*[labels[col][row] for col in range(game.slot_machine.cols)])

        console.print(Panel(table, title="Reels", border_style="cyan"))
        return

    write()
    write("+" + "+".join(["--------"] * len(labels)) + "+")
    for row in range(game.slot_machine.rows):
        row_values = [labels[col][row].center(8) for col in range(game.slot_machine.cols)]
        write("|" + "|".join(row_values) + "|")
    write("+" + "+".join(["--------"] * len(labels)) + "+")


def show_spin_animation():
    if not RICH_AVAILABLE:
        return

    with console.status("[bold cyan]Reels spinning...[/bold cyan]", spinner="dots"):
        time.sleep(0.5)


def show_spin_result(game, result):
    show_reels(game, result.columns)

    if result.free_spin_used:
        write("[cyan]Free spin used. No wager deducted.[/cyan]")

    if result.total_winnings:
        write(f"[green]You won ${result.total_winnings}.[/green]")
    else:
        write("[yellow]No win this spin.[/yellow]")

    for line in result.line_wins:
        labels = " ".join(game.slot_machine.pay_table.labels_for_line(line.symbols))
        jackpot = " jackpot" if line.jackpot_hit else ""
        write(f"  {line.name}: {labels} pays ${line.amount}{jackpot}")

    if result.scatter_bonus:
        write(f"  Scatter bonus pays ${result.scatter_bonus}")

    for message in result.messages:
        write(f"  {message}")


def show_paytable(game):
    rows = game.slot_machine.pay_table.symbol_rows()

    if RICH_AVAILABLE:
        table = Table(title="Paytable")
        table.add_column("Symbol")
        table.add_column("Label")
        table.add_column("Weight", justify="right")
        table.add_column("Payout", justify="right")

        for row in rows:
            payout = f"{row['payout']}x" if row["payout"] else "special"
            table.add_row(row["symbol"], row["label"], str(row["weight"]), payout)

        console.print(table)
    else:
        write("\nPaytable:")
        for row in rows:
            payout = f"{row['payout']}x" if row["payout"] else "special"
            write(
                f"  {row['symbol']:<8} {row['label']:<5} weight {row['weight']:<2} payout {payout}"
            )

    config = game.slot_machine.config
    write(
        f"Wilds substitute for line symbols. Scatters award {config['free_spins_award']} free spins."
    )
    write("Natural 7s and diamonds trigger jackpot bonuses.")


def show_stats(player):
    stats = player.stats

    if RICH_AVAILABLE:
        table = Table(title="Session Stats")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        rows = stats_rows(player)
        for label, value in rows:
            table.add_row(label, value)
        console.print(table)
        return

    write("\nSession stats:")
    for label, value in stats_rows(player):
        write(f"  {label}: {value}")


def stats_rows(player):
    stats = player.stats
    return [
        ("Balance", f"${player.balance}"),
        ("Spins", str(stats.spins)),
        ("Total wagered", f"${stats.total_wagered}"),
        ("Total won", f"${stats.total_won}"),
        ("Net profit/loss", f"${stats.net}"),
        ("Biggest win", f"${stats.biggest_win}"),
        ("Jackpots", str(stats.jackpots)),
        ("Free spins won", str(stats.free_spins_won)),
        ("Free spins used", str(stats.free_spins_used)),
        ("Win rate", f"{stats.win_rate:.0%}"),
    ]


def show_history(player, limit=8):
    if not player.history:
        write("[yellow]No spins in history yet.[/yellow]")
        return

    recent = player.history[-limit:]

    if RICH_AVAILABLE:
        table = Table(title=f"Last {len(recent)} Spins")
        table.add_column("Time")
        table.add_column("Bet", justify="right")
        table.add_column("Won", justify="right")
        table.add_column("Net", justify="right")
        table.add_column("Balance", justify="right")

        for item in recent:
            table.add_row(
                item["time"],
                f"${item['total_bet']}",
                f"${item['won']}",
                f"${item['net']}",
                f"${item['balance_after']}",
            )

        console.print(table)
        return

    write(f"\nLast {len(recent)} spins:")
    for item in recent:
        write(
            f"  {item['time']} | bet ${item['total_bet']} | won ${item['won']} | "
            f"net ${item['net']} | balance ${item['balance_after']}"
        )


def play_spin(game, player):
    lines = ask_paylines(game)
    bet = ask_bet(game)

    try:
        show_spin_animation()
        result = game.spin(player, lines, bet)
    except ValueError as error:
        write(f"[red]{error}[/red]")
        return

    show_spin_result(game, result)


def main():
    game = SlotGame()
    player = ask_player()

    while player.balance >= game.slot_machine.min_bet or player.free_spins:
        answer = show_menu(player)

        if answer == "q":
            break
        if answer == "p":
            show_paytable(game)
            continue
        if answer == "s":
            show_stats(player)
            continue
        if answer == "h":
            show_history(player)
            continue
        if answer == "v":
            player.save(SAVE_FILE)
            write(f"[green]Saved to {SAVE_FILE}.[/green]")
            continue
        if answer == "l":
            if SAVE_FILE.exists():
                player = Player.load(SAVE_FILE)
                write(f"[green]Loaded {player.name}.[/green]")
            else:
                write("[yellow]No save file found.[/yellow]")
            continue
        if answer:
            write("[red]Choose Enter, p, s, h, v, l, or q.[/red]")
            continue

        play_spin(game, player)

    show_stats(player)
    write(f"\nYou left with ${player.balance}.")


if __name__ == "__main__":
    main()
