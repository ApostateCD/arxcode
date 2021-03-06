# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-23 02:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def convert_help_entries_and_posts_to_kb_items(apps, schema_editor):
    """
    This data migration is for converting existing lore/theme notes that are scattered between
    HelpEntry objects and Msg objects into KBItem objects, with KBCategory objects also created
    for their categories.
    """
    from django.template.defaultfilters import slugify
    from datetime import datetime

    # helpdesk knowledge base models
    KBItem = apps.get_model("helpdesk", "KBItem")
    KBCategory = apps.get_model("helpdesk", "KBCategory")
    # titles for KBItems to prevent duplicates
    kb_item_titles = set()
    kb_items = []
    # models for the Board and Post objects
    ObjectDB = apps.get_model("objects", "ObjectDB")
    Msg = apps.get_model("comms", "Msg")
    # model for lore stored in help files
    HelpEntry = apps.get_model("help", "HelpEntry")
    help_lore_categories = [
        "Expectations",
        "expectations",
        "culture",
        "gods",
        "lore",
        "knowledge",
    ]
    # convert help entries
    entries = HelpEntry.objects.filter(db_help_category__in=help_lore_categories)
    # time for last_updated
    now = datetime.now()
    for entry in entries:
        title = entry.db_key
        # if the title is already present, we have to disambiguate it
        while title.lower() in kb_item_titles:
            title += "x"
        kb_item_titles.add(title.lower())
        category, _ = KBCategory.objects.get_or_create(
            title=entry.db_help_category.title(),
            slug=slugify(entry.db_help_category.title()),
        )
        if "skill" in entry.db_lock_storage:
            question = "What would someone know with a skill of this rating?"
        else:
            question = ""
        kb_items.append(
            KBItem(
                title=title,
                category=category,
                answer=entry.db_entrytext,
                question=question,
                last_updated=now,
            )
        )
    try:
        board = ObjectDB.objects.filter(
            db_typeclass_path="typeclasses.bulletin_board.bboard.BBoard"
        ).get(db_key__iexact="theme questions")
    except Exception:
        return
    posts = Msg.objects.filter(db_receivers_objects=board)
    for post in posts:
        title = post.db_header.title()
        # getting the 'category' is much more tricky here from the subject. We'll do the first word as a best guess.
        first_word = title.split()[0]
        category, _ = KBCategory.objects.get_or_create(
            title=first_word.capitalize(), slug=slugify(first_word.capitalize())
        )
        while title.lower() in kb_item_titles:
            title += "x"
        kb_item_titles.add(title.lower())
        kb_items.append(
            KBItem(
                title=title,
                category=category,
                question=post.db_message,
                last_updated=now,
            )
        )
    # create all the KBItem objects
    KBItem.objects.bulk_create(kb_items)
    # delete the old querysets
    entries.delete()
    board.delete()
    posts.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0013_ticket_goal_update"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="kbitem",
            name="recommendations",
        ),
        migrations.RemoveField(
            model_name="kbitem",
            name="votes",
        ),
        migrations.AddField(
            model_name="kbcategory",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subcategories",
                to="helpdesk.KBCategory",
            ),
        ),
        migrations.AddField(
            model_name="kbcategory",
            name="search_tags",
            field=models.ManyToManyField(
                blank=True, related_name="kb_categories", to="character.SearchTag"
            ),
        ),
        migrations.AddField(
            model_name="kbitem",
            name="search_tags",
            field=models.ManyToManyField(
                blank=True, related_name="kb_items", to="character.SearchTag"
            ),
        ),
        migrations.AddField(
            model_name="ticket",
            name="kb_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="helpdesk.KBCategory",
            ),
        ),
        migrations.AlterField(
            model_name="kbcategory",
            name="description",
            field=models.TextField(blank=True, verbose_name="Description"),
        ),
        migrations.AlterField(
            model_name="kbcategory",
            name="slug",
            field=models.SlugField(unique=True, verbose_name="Slug"),
        ),
        migrations.AlterField(
            model_name="kbcategory",
            name="title",
            field=models.CharField(max_length=100, unique=True, verbose_name="Title"),
        ),
        migrations.AlterField(
            model_name="kbitem",
            name="answer",
            field=models.TextField(blank=True, verbose_name="Answer"),
        ),
        migrations.AlterField(
            model_name="kbitem",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="kb_items",
                to="helpdesk.KBCategory",
                verbose_name="Category",
            ),
        ),
        migrations.AlterField(
            model_name="kbitem",
            name="question",
            field=models.TextField(blank=True, verbose_name="Question"),
        ),
        migrations.AlterField(
            model_name="kbitem",
            name="title",
            field=models.CharField(max_length=100, unique=True, verbose_name="Title"),
        ),
        migrations.RunPython(convert_help_entries_and_posts_to_kb_items, elidable=True),
    ]
